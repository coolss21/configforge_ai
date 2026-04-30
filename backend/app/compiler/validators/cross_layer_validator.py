"""
Cross-layer validator.
Returns (errors: list, checks_count: int).
Every single check performed increments checks_count.
Target: >= 20 checks for a typical CRM config.
"""

# ── Helpers ────────────────────────────────────────────────────────────────────

def _match_table(tables_lower: dict, name: str):
    """Find a DB table dict matching entity name (singular/plural tolerant)."""
    n = name.lower()
    return (
        tables_lower.get(n)
        or tables_lower.get(n + "s")
        or tables_lower.get(n.rstrip("s") if len(n) > 2 else n)
        or tables_lower.get(n + "es")
    )


def _db_fields(tables_lower: dict, entity: str) -> set:
    tbl = _match_table(tables_lower, entity)
    if not tbl:
        return set()
    return {f["name"].lower() for f in tbl.get("fields", [])}


def _dummy_val(field: dict):
    ft = field.get("type", "TEXT").upper()
    if "INT" in ft:
        return 1
    if "BOOL" in ft:
        return 1
    return "test_value"


class CrossLayerValidator:
    def validate(self, config: dict) -> tuple:
        """Returns (errors: list, checks_run: int)."""
        errors  = []
        checks  = 0

        intent  = config.get("intent", {})
        db      = config.get("database", {})
        api     = config.get("api", {})
        ui      = config.get("ui", {})
        auth    = config.get("auth", {})
        logic   = config.get("business_logic", {})

        # Build index structures
        tables_lower  = {t["name"].lower(): t for t in db.get("tables", [])}
        all_tables    = set(tables_lower.keys())
        roles         = {r["name"] for r in auth.get("roles", [])}
        api_paths     = {e["path"] for e in api.get("endpoints", [])}

        # ════════════════════════════════════════════════════════
        # 1. Every DB table must have an `id` primary key
        # ════════════════════════════════════════════════════════
        for tbl in db.get("tables", []):
            checks += 1
            pk_fields = [f for f in tbl.get("fields", []) if f.get("primary_key")]
            if not pk_fields:
                errors.append({
                    "code": "TABLE_MISSING_PK",
                    "severity": "high", "layer": "cross_layer",
                    "message": f"Table '{tbl['name']}' has no primary key field.",
                    "repair_strategy": "add_pk_to_table",
                    "context": {"entity": tbl["name"]}
                })

        # ════════════════════════════════════════════════════════
        # 2. Intent entity → DB checks
        # ════════════════════════════════════════════════════════
        for entity in intent.get("entities", []):
            ename = entity.get("name", "").lower()

            # 2a. Entity must exist as DB table
            checks += 1
            db_tbl = _match_table(tables_lower, ename)
            if db_tbl is None:
                errors.append({
                    "code": "INTENT_ENTITY_MISSING_IN_DB",
                    "severity": "high", "layer": "cross_layer",
                    "message": f"Intent entity '{ename}' has no matching DB table. Available: {sorted(all_tables)}",
                    "repair_strategy": "add_missing_db_table",
                    "context": {"entity": ename}
                })
                continue

            # 2b. Every intent field must exist in DB table
            db_flds = _db_fields(tables_lower, ename)
            for fld in entity.get("fields", []):
                fname = fld.get("name", "").lower()
                checks += 1
                if fname and fname not in db_flds:
                    errors.append({
                        "code": "INTENT_FIELD_MISSING_IN_DB",
                        "severity": "high", "layer": "cross_layer",
                        "message": (
                            f"Intent entity '{ename}' field '{fname}' missing from "
                            f"DB table '{db_tbl['name']}'. DB has: {sorted(db_flds)}"
                        ),
                        "repair_strategy": "add_missing_db_field",
                        "context": {"entity": ename, "field": fname}
                    })

        # ════════════════════════════════════════════════════════
        # 3. Auth role completeness: intent.roles ⊆ auth.roles
        # ════════════════════════════════════════════════════════
        for role in intent.get("roles", []):
            checks += 1
            if role not in roles:
                errors.append({
                    "code": "AUTH_ROLE_MISMATCH",
                    "severity": "high", "layer": "cross_layer",
                    "message": f"Intent role '{role}' not in auth.roles. Auth has: {sorted(roles)}",
                    "repair_strategy": "auth_role_mismatch",
                    "context": {"missing_role": role}
                })

        # ════════════════════════════════════════════════════════
        # 4. auth_required must have non-empty access_rules
        # ════════════════════════════════════════════════════════
        checks += 1
        if auth.get("auth_required", False) and not auth.get("access_rules", []):
            errors.append({
                "code": "AUTH_NO_ACCESS_RULES",
                "severity": "high", "layer": "cross_layer",
                "message": "auth_required=true but access_rules is empty.",
                "repair_strategy": "add_default_access_rules",
                "context": {}
            })

        # ════════════════════════════════════════════════════════
        # 5. access_rule role + resource must exist
        # ════════════════════════════════════════════════════════
        for rule in auth.get("access_rules", []):
            # 5a. role exists
            checks += 1
            r = rule.get("role", "")
            if r and r not in roles:
                errors.append({
                    "code": "ACCESS_RULE_ROLE_MISSING",
                    "severity": "high", "layer": "cross_layer",
                    "message": f"access_rule role '{r}' not in auth.roles.",
                    "repair_strategy": "auth_role_mismatch",
                    "context": {"missing_role": r}
                })
            # 5b. resource is a real DB table
            checks += 1
            res = rule.get("resource", "")
            if res and not _match_table(tables_lower, res):
                errors.append({
                    "code": "ACCESS_RULE_RESOURCE_MISSING",
                    "severity": "medium", "layer": "cross_layer",
                    "message": f"access_rule resource '{res}' not in DB tables.",
                    "repair_strategy": "api_to_db_mismatch",
                    "context": {"entity": res, "path": "access_rule"}
                })

        # ════════════════════════════════════════════════════════
        # 6. API endpoint checks
        # ════════════════════════════════════════════════════════
        for ep in api.get("endpoints", []):
            entity   = (ep.get("entity") or "").strip()
            path     = ep.get("path", "")
            req_role = ep.get("required_role")

            # 6a. API entity must exist in DB
            if entity:
                checks += 1
                if not _match_table(tables_lower, entity):
                    errors.append({
                        "code": "API_ENTITY_MISSING",
                        "severity": "high", "layer": "cross_layer",
                        "message": f"API '{path}' entity '{entity}' not in DB.",
                        "repair_strategy": "api_to_db_mismatch",
                        "context": {"entity": entity, "path": path}
                    })

            # 6b. required_role must be in auth.roles
            if req_role:
                checks += 1
                if req_role not in roles:
                    errors.append({
                        "code": "API_ROLE_MISSING",
                        "severity": "high", "layer": "cross_layer",
                        "message": f"API '{path}' required_role '{req_role}' not in auth.roles.",
                        "repair_strategy": "auth_role_mismatch",
                        "context": {"missing_role": req_role}
                    })

            # 6c. request_body fields must exist in DB table
            if entity:
                db_flds = _db_fields(tables_lower, entity)
                for fname in ep.get("request_body", {}):
                    # skip derived fields like 'password'
                    if fname.lower() in ("password",):
                        continue
                    checks += 1
                    if db_flds and fname.lower() not in db_flds:
                        errors.append({
                            "code": "API_REQUEST_FIELD_MISSING_IN_DB",
                            "severity": "medium", "layer": "cross_layer",
                            "message": (
                                f"API '{path}' request_body field '{fname}' "
                                f"not in DB table '{entity}'."
                            ),
                            "repair_strategy": "add_missing_db_field",
                            "context": {"entity": entity, "field": fname}
                        })

        # ════════════════════════════════════════════════════════
        # 7. UI page / component checks
        # ════════════════════════════════════════════════════════
        for page in ui.get("pages", []):
            # 7a. page required_role
            req_role = page.get("required_role")
            if req_role:
                checks += 1
                if req_role not in roles:
                    errors.append({
                        "code": "UI_ROLE_MISSING",
                        "severity": "high", "layer": "cross_layer",
                        "message": f"UI page '{page.get('route')}' required_role '{req_role}' not in auth.roles.",
                        "repair_strategy": "auth_role_mismatch",
                        "context": {"missing_role": req_role}
                    })

            for comp in page.get("components", []):
                entity  = (comp.get("entity") or "").strip()
                api_ep  = comp.get("api_endpoint")

                # 7b. component entity must exist in DB
                if entity:
                    checks += 1
                    if not _match_table(tables_lower, entity):
                        errors.append({
                            "code": "UI_ENTITY_MISSING",
                            "severity": "high", "layer": "cross_layer",
                            "message": f"UI component entity '{entity}' not in DB.",
                            "repair_strategy": "ui_to_db_mismatch",
                            "context": {"entity": entity}
                        })
                    else:
                        # 7c. component fields must exist in DB
                        db_flds = _db_fields(tables_lower, entity)
                        for fname in comp.get("fields", []):
                            # skip derived fields like 'password'
                            if fname.lower() in ("password",):
                                continue
                            checks += 1
                            if db_flds and fname.lower() not in db_flds:
                                errors.append({
                                    "code": "UI_FIELD_MISSING_IN_DB",
                                    "severity": "low", "layer": "cross_layer",
                                    "message": (
                                        f"UI component field '{fname}' for entity '{entity}' "
                                        f"not in DB table."
                                    ),
                                    "repair_strategy": "add_missing_db_field",
                                    "context": {"entity": entity, "field": fname}
                                })

                # 7d. api_endpoint must exist in API schema
                if api_ep:
                    checks += 1
                    if api_ep not in api_paths:
                        errors.append({
                            "code": "UI_API_MISSING",
                            "severity": "medium", "layer": "cross_layer",
                            "message": f"UI component api_endpoint '{api_ep}' not in API schema.",
                            "repair_strategy": "ui_to_api_mismatch",
                            "context": {"endpoint": api_ep}
                        })

        # ════════════════════════════════════════════════════════
        # 8. Business logic referential integrity
        # ════════════════════════════════════════════════════════
        for rule in logic.get("rules", []):
            rule_name = rule.get("name", "unknown")
            combined  = " ".join([
                rule.get("name", ""),
                rule.get("trigger", ""),
                rule.get("condition", ""),
                rule.get("action", ""),
            ]).lower()

            # 8a. audit_log reference → audit_log table must exist
            checks += 1
            if "audit_log" in combined:
                if "audit_log" not in all_tables and "audit_logs" not in all_tables:
                    errors.append({
                        "code": "LOGIC_AUDIT_LOG_TABLE_MISSING",
                        "severity": "high", "layer": "cross_layer",
                        "message": (
                            f"Business rule '{rule_name}' references audit_log "
                            f"but no audit_log/audit_logs table in DB."
                        ),
                        "repair_strategy": "add_audit_log_table",
                        "context": {"table": "audit_log", "rule": rule_name}
                    })

            # 8b. soft_delete / deleted_at reference → deleted_at field must exist
            checks += 1
            if "deleted_at" in combined or "soft_delete" in combined or "soft delete" in combined:
                trigger = rule.get("trigger", "").lower()
                matched = False
                for tbl_name_lower, tbl in tables_lower.items():
                    if tbl_name_lower in trigger or tbl_name_lower.rstrip("s") in trigger:
                        flds = {f["name"].lower() for f in tbl.get("fields", [])}
                        if "deleted_at" not in flds:
                            errors.append({
                                "code": "LOGIC_SOFT_DELETE_FIELD_MISSING",
                                "severity": "high", "layer": "cross_layer",
                                "message": (
                                    f"Business rule '{rule_name}' uses soft-delete but "
                                    f"table '{tbl['name']}' has no 'deleted_at' field."
                                ),
                                "repair_strategy": "add_soft_delete_field",
                                "context": {"entity": tbl["name"], "field": "deleted_at"}
                            })
                        matched = True
                        break
                # If no table matched but soft_delete referenced, still a check
                if not matched:
                    checks += 1  # count the lookup as a check

        # ════════════════════════════════════════════════════════
        # 9. Requested Feature Checks
        # ════════════════════════════════════════════════════════
        features_lower = [f.lower() for f in intent.get("features", [])]
        
        # 9a. Payments check
        if "payments" in features_lower or "payment" in features_lower:
            checks += 1
            if "payments" not in all_tables:
                errors.append({
                    "code": "MISSING_PAYMENT_SCHEMA",
                    "severity": "high", "layer": "cross_layer",
                    "message": "Prompt requested payments but 'payments' table is missing.",
                    "repair_strategy": "add_payment_schema",
                    "context": {"feature": "payments"}
                })
                
        # 9b. Subscriptions check
        if "premium plan" in features_lower or "subscriptions" in features_lower or "subscription" in features_lower:
            checks += 1
            if "plans" not in all_tables and "subscriptions" not in all_tables:
                errors.append({
                    "code": "MISSING_SUBSCRIPTION_SCHEMA",
                    "severity": "high", "layer": "cross_layer",
                    "message": "Prompt requested premium plans but 'plans' or 'subscriptions' tables are missing.",
                    "repair_strategy": "add_subscription_schema",
                    "context": {"feature": "premium"}
                })
                
        # 9c. Analytics check
        if "admin analytics" in features_lower or "analytics" in features_lower:
            checks += 1
            has_analytics_api = any("analytics" in ep.get("path", "") for ep in api.get("endpoints", []))
            has_analytics_ui = any("analytics" in page.get("route", "") for page in ui.get("pages", []))
            if not has_analytics_api and not has_analytics_ui:
                errors.append({
                    "code": "MISSING_ANALYTICS_SCHEMA",
                    "severity": "high", "layer": "cross_layer",
                    "message": "Prompt requested analytics but no analytics endpoint or UI page is present.",
                    "repair_strategy": "add_analytics_schema",
                    "context": {"feature": "analytics"}
                })

        # ════════════════════════════════════════════════════════
        # 10. Empty UI Components
        # ════════════════════════════════════════════════════════
        for page in ui.get("pages", []):
            checks += 1
            if not page.get("components"):
                errors.append({
                    "code": "EMPTY_UI_COMPONENTS",
                    "severity": "high", "layer": "cross_layer",
                    "message": f"UI page '{page.get('route')}' has no components.",
                    "repair_strategy": "add_default_components",
                    "context": {"route": page.get("route"), "layout": page.get("layout")}
                })

        # ════════════════════════════════════════════════════════
        # 11. Empty Architecture Modules
        # ════════════════════════════════════════════════════════
        arch_modules = config.get("architecture", {}).get("modules", [])
        for mod in arch_modules:
            checks += 1
            if not mod.get("entities_used"):
                errors.append({
                    "code": "EMPTY_ARCHITECTURE_MODULE",
                    "severity": "high", "layer": "cross_layer",
                    "message": f"Architecture module '{mod.get('name')}' has empty entities_used.",
                    "repair_strategy": "populate_architecture",
                    "context": {"module": mod.get("name")}
                })

        # ════════════════════════════════════════════════════════
        # 12. Unrequested Major Features
        # ════════════════════════════════════════════════════════
        features_lower = [f.lower() for f in intent.get("features", [])]
        has_payments_intent = any(w in f for f in features_lower for w in ["payment", "billing"])
        has_premium_intent = any(w in f for f in features_lower for w in ["premium", "subscription", "plan"])
        
        checks += 1
        if not has_payments_intent and "payments" in all_tables:
            errors.append({
                "code": "UNREQUESTED_MAJOR_FEATURE",
                "severity": "high", "layer": "cross_layer",
                "message": "Payments table generated but not requested in prompt features.",
                "repair_strategy": "remove_unrequested_feature",
                "context": {"feature": "payments"}
            })
            
        checks += 1
        if not has_premium_intent and ("subscriptions" in all_tables or "plans" in all_tables):
            errors.append({
                "code": "UNREQUESTED_MAJOR_FEATURE",
                "severity": "high", "layer": "cross_layer",
                "message": "Subscriptions/Plans generated but not requested in prompt features.",
                "repair_strategy": "remove_unrequested_feature",
                "context": {"feature": "subscriptions"}
            })

        # ════════════════════════════════════════════════════════
        # 13. Weak DB Schema
        # ════════════════════════════════════════════════════════
        for tbl in db.get("tables", []):
            checks += 1
            if len(tbl.get("fields", [])) <= 1:
                errors.append({
                    "code": "WEAK_DB_SCHEMA",
                    "severity": "high", "layer": "cross_layer",
                    "message": f"Table '{tbl.get('name')}' only has {len(tbl.get('fields', []))} fields.",
                    "repair_strategy": "enhance_db_schema",
                    "context": {"entity": tbl.get("name")}
                })


        # ════════════════════════════════════════════════════════
        # 14. Prompt Coverage (TEMPLATE_PROMPT_MISMATCH)
        # ════════════════════════════════════════════════════════
        checks += 1
        app_type = intent.get("app_type", "")
        template_used = intent.get("template_used", "")
        app_name = intent.get("app_name", "")
        flags = intent.get("requested_feature_flags", {})
        
        # 10. Prompt Coverage
        # Check payments
        if flags.get("payments"):
            if "payments" not in all_tables:
                errors.append({
                    "code": "MISSING_REQUESTED_FEATURE",
                    "severity": "high", "layer": "cross_layer",
                    "message": "Payments requested but no payments table found.",
                    "repair_strategy": "add_missing_logic_table",
                    "context": {"table": "payments"}
                })
        else:
            if "payments" in all_tables:
                errors.append({
                    "code": "UNREQUESTED_MAJOR_FEATURE",
                    "severity": "medium", "layer": "cross_layer",
                    "message": "Payments table exists but payments were not requested.",
                    "repair_strategy": "remove_unrequested_feature",
                    "context": {"feature": "payments"}
                })
                
        # Check sensitive domain
        if flags.get("sensitive_domain"):
            if not auth.get("auth_required"):
                errors.append({
                    "code": "MISSING_REQUESTED_FEATURE",
                    "severity": "high", "layer": "cross_layer",
                    "message": "Auth required for sensitive domain.",
                    "repair_strategy": "set_auth_required_true",
                    "context": {}
                })
            if "audit_logs" not in all_tables:
                errors.append({
                    "code": "MISSING_REQUESTED_FEATURE",
                    "severity": "high", "layer": "cross_layer",
                    "message": "Sensitive domain requires audit_logs table.",
                    "repair_strategy": "add_missing_logic_table",
                    "context": {"table": "audit_logs"}
                })
                
        # Descriptions
        for ent in intent.get("entities", []):
            for f in ent.get("fields", []):
                if not f.get("description"):
                    errors.append({
                        "code": "MISSING_FIELD_DESCRIPTION",
                        "severity": "low", "layer": "cross_layer",
                        "message": f"Field {f.get('name')} missing description.",
                        "repair_strategy": "add_field_description",
                        "context": {"entity": ent.get("name"), "field": f.get("name")}
                    })



        # 11. Custom App entity coverage
        checks += 1
        intent_entity_names = [e.get("name","").lower() for e in intent.get("entities", [])]
        non_system_tables = [t for t in all_tables if t not in ("users","audit_logs","payments","plans","subscriptions")]
        if len(intent_entity_names) > 1 and non_system_tables == ["items"]:
            errors.append({"code": "TEMPLATE_PROMPT_MISMATCH", "severity": "high", "layer": "cross_layer",
                "message": f"Detailed app collapsed to items. Expected: {intent_entity_names}",
                "repair_strategy": "expand_custom_entities", "context": {"expected_entities": intent_entity_names}})

        # 12. Every intent entity must have DB coverage
        for ename in intent_entity_names:
            checks += 1
            table_name = ename if ename.endswith("s") else ename + "s"
            if ename not in all_tables and table_name not in all_tables:
                errors.append({"code": "MISSING_REQUESTED_FEATURE", "severity": "high", "layer": "cross_layer",
                    "message": f"Intent entity '{ename}' has no DB table.",
                    "repair_strategy": "add_missing_db_table", "context": {"entity": ename}})

        return errors, checks
