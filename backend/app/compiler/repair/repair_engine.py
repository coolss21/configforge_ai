import logging
import time
from app.compiler.validators.master_validator import MasterValidator

logger = logging.getLogger("configforge.repair")

# ── Audit log table template ───────────────────────────────────────────────────
_AUDIT_LOG_TABLE = {
    "name": "audit_log",
    "fields": [
        {"name": "id",         "type": "INTEGER", "primary_key": True,  "nullable": False, "unique": True},
        {"name": "table_name", "type": "TEXT",    "primary_key": False, "nullable": False, "unique": False},
        {"name": "record_id",  "type": "INTEGER", "primary_key": False, "nullable": False, "unique": False},
        {"name": "action",     "type": "TEXT",    "primary_key": False, "nullable": False, "unique": False},
        {"name": "changed_by", "type": "INTEGER", "primary_key": False, "nullable": True,  "unique": False},
        {"name": "changed_at", "type": "TEXT",    "primary_key": False, "nullable": True,  "unique": False},
    ]
}


def _tables_lower_map(config: dict) -> dict:
    return {t["name"].lower(): t for t in config.get("database", {}).get("tables", [])}


class RepairEngine:
    """
    Fully deterministic repair engine — no LLM calls.
    Each error code maps to a targeted fix applied directly to the config.
    """

    async def run(self, config: dict, mode: str) -> dict:
        validator   = MasterValidator()
        start       = time.perf_counter()
        report      = validator.validate(config)
        config["validation_report"] = report

        if report["is_valid"]:
            config["repair_report"] = self._empty_report()
            return config

        max_rounds     = 1 if mode == "fast" else 3
        current_round  = 0
        repair_log:    list = []
        repaired_layers: set = set()

        while not report["is_valid"] and current_round < max_rounds:
            current_round += 1
            logger.info(f"Repair round {current_round} — {report['error_count']} errors")

            # Deduplicate errors by (code, context) so we don't apply same fix twice
            seen = set()
            for err in list(report["errors"]):
                strategy = err.get("repair_strategy", "")
                ctx      = err.get("context", {})
                dedup_key = (err.get("code", ""), str(sorted(ctx.items())))
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                fixed = self._apply_repair(config, strategy, ctx, err)

                code  = err.get("code", "UNKNOWN")
                layer = err.get("layer", "unknown")
                repair_log.append({
                    "round":         current_round,
                    "layer":         layer,
                    "error_code":    code,
                    "strategy":      strategy,
                    "deterministic": True,
                    "success":       fixed
                })
                if fixed:
                    repaired_layers.add(layer)

            report = validator.validate(config)
            config["validation_report"] = report

        elapsed_ms = round((time.perf_counter() - start) * 1000, 3)

        config["repair_report"] = {
            "repair_attempted":  current_round > 0,
            "repair_rounds":     current_round,
            "repaired_layers":   sorted(repaired_layers),
            "unresolved_errors": report["errors"] if not report["is_valid"] else [],
            "repair_log":        repair_log,
            "repair_time_ms":    elapsed_ms
        }
        return config

    # ── Strategy dispatcher ────────────────────────────────────────────────────
    def _apply_repair(self, config: dict, strategy: str, ctx: dict, err: dict) -> bool:
        if strategy == "add_missing_db_table":
            return self._add_db_table(config, ctx.get("entity", "unknown"))

        if strategy == "add_missing_db_field":
            return self._add_db_field(config, ctx.get("entity", ""), ctx.get("field", ""))

        if strategy == "auth_role_mismatch":
            missing = ctx.get("missing_role") or self._extract_quoted(err.get("message", ""))
            return self._add_auth_role(config, missing)

        if strategy == "add_default_access_rules":
            return self._add_access_rules(config)

        if strategy == "set_auth_required_true":
            config.setdefault("auth", {})["auth_required"] = True
            return True

        if strategy == "api_to_db_mismatch":
            return self._add_db_table(config, ctx.get("entity", ""))

        if strategy == "ui_to_api_mismatch":
            return self._remove_bad_ui_endpoint(config, ctx.get("endpoint", ""))

        if strategy == "ui_to_db_mismatch":
            return self._remove_bad_ui_entity(config, ctx.get("entity", ""))

        if strategy == "block_execution":
            return True   # enforced in executor

        # ── Fix 3: Business logic repair ──────────────────────────────────────
        if strategy == "add_audit_log_table":
            return self._add_audit_log_table(config)

        if strategy == "add_soft_delete_field":
            entity = ctx.get("entity", "")
            return self._add_db_field(config, entity, "deleted_at")

        if strategy == "add_missing_logic_table":
            table = ctx.get("table", "")
            if table == "audit_log":
                return self._add_audit_log_table(config)
            return self._add_db_table(config, table)

        return False

    # ── Atomic repair helpers ──────────────────────────────────────────────────
    def _add_db_table(self, config: dict, entity: str) -> bool:
        if not entity:
            return False
        existing = {t["name"].lower() for t in config["database"].get("tables", [])}
        if entity.lower() in existing:
            return True   # already present
        config["database"].setdefault("tables", []).append({
            "name": entity,
            "fields": [
                {"name": "id",         "type": "INTEGER", "primary_key": True,  "nullable": False, "unique": True},
                {"name": "name",       "type": "TEXT",    "primary_key": False, "nullable": False, "unique": False},
                {"name": "created_at", "type": "TEXT",    "primary_key": False, "nullable": True,  "unique": False},
                {"name": "updated_at", "type": "TEXT",    "primary_key": False, "nullable": True,  "unique": False},
            ]
        })
        return True

    def _add_db_field(self, config: dict, entity: str, field: str) -> bool:
        if not entity or not field:
            return False
        e_lower = entity.lower()
        for tbl in config["database"].get("tables", []):
            t_lower = tbl["name"].lower()
            if t_lower in (e_lower, e_lower + "s", e_lower.rstrip("s"), e_lower + "es"):
                existing = {f["name"].lower() for f in tbl.get("fields", [])}
                if field.lower() not in existing:
                    tbl.setdefault("fields", []).append({
                        "name": field, "type": "TEXT",
                        "primary_key": False, "nullable": True, "unique": False
                    })
                return True
        return False

    def _add_auth_role(self, config: dict, role: str) -> bool:
        if not role:
            return False
        auth  = config.setdefault("auth", {})
        roles = auth.setdefault("roles", [])
        if role not in {r["name"] for r in roles}:
            roles.append({"name": role, "permissions": ["read"]})
        return True

    def _add_access_rules(self, config: dict) -> bool:
        auth = config.setdefault("auth", {})
        if auth.get("access_rules"):
            return True
        role_names = [r["name"] for r in auth.get("roles", [])]
        table_names = [t["name"] for t in config.get("database", {}).get("tables", [])]
        rules = []
        for role in role_names:
            for resource in table_names:
                actions = (
                    ["read", "create", "update", "delete"]
                    if role == "admin"
                    else ["read", "create"]
                )
                rules.append({"role": role, "resource": resource, "actions": actions})
        auth["access_rules"] = rules
        return True

    def _add_audit_log_table(self, config: dict) -> bool:
        existing = {t["name"].lower() for t in config["database"].get("tables", [])}
        if "audit_log" in existing or "audit_logs" in existing:
            return True
        config["database"].setdefault("tables", []).append(dict(_AUDIT_LOG_TABLE))
        return True

    def _remove_bad_ui_endpoint(self, config: dict, bad_ep: str) -> bool:
        api_paths = {e["path"] for e in config.get("api", {}).get("endpoints", [])}
        for page in config.get("ui", {}).get("pages", []):
            for comp in page.get("components", []):
                if comp.get("api_endpoint") == bad_ep and bad_ep not in api_paths:
                    comp.pop("api_endpoint", None)
        return True

    def _remove_bad_ui_entity(self, config: dict, entity: str) -> bool:
        valid = {t["name"].lower() for t in config.get("database", {}).get("tables", [])}
        for page in config.get("ui", {}).get("pages", []):
            for comp in page.get("components", []):
                if comp.get("entity", "").lower() == entity.lower() and entity.lower() not in valid:
                    comp.pop("entity", None)
        return True

    @staticmethod
    def _extract_quoted(text: str) -> str:
        parts = text.split("'")
        return parts[1] if len(parts) >= 3 else ""

    @staticmethod
    def _empty_report() -> dict:
        return {
            "repair_attempted":  False,
            "repair_rounds":     0,
            "repaired_layers":   [],
            "unresolved_errors": [],
            "repair_log":        [],
            "repair_time_ms":    0.0
        }
