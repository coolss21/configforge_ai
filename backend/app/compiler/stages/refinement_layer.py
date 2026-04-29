import time
from datetime import datetime
from app.core.utils import generate_hash

class RefinementLayer:
    def run(self, intent, arch, db, api, ui, auth, logic, mode, trace_id, pipeline_trace) -> dict:
        # Normalization and combining logic
        
        # Sort tables by name, fields by name (id first)
        if "tables" in db:
            db["tables"] = sorted(db["tables"], key=lambda x: x.get("name", ""))
            for table in db["tables"]:
                if "fields" in table:
                    table["fields"] = sorted(table["fields"], key=lambda f: (f.get("name") != "id", f.get("name", "")))
        
        # Sort API endpoints
        if "endpoints" in api:
            api["endpoints"] = sorted(api["endpoints"], key=lambda x: (x.get("path", ""), x.get("method", "")))
            
        # Sort UI pages
        if "pages" in ui:
            ui["pages"] = sorted(ui["pages"], key=lambda x: x.get("route", ""))
            
        # Sort Auth roles
        if "roles" in auth:
            auth["roles"] = sorted(auth["roles"], key=lambda x: x.get("name", ""))
            
        # Sort Business logic rules
        if "rules" in logic:
            # Fast mode sanitizer: strip advanced rules if DB support is missing
            if mode == "fast":
                all_tables = {t.get("name", "").lower() for t in db.get("tables", [])}
                has_audit = "audit_log" in all_tables or "audit_logs" in all_tables

                valid_rules = []
                for rule in logic["rules"]:
                    r_str = str(rule).lower()
                    if "audit" in r_str and not has_audit:
                        continue
                    
                    if "soft_delete" in r_str or "deleted_at" in r_str:
                        # check if the target table has deleted_at
                        has_deleted_at = False
                        for t in db.get("tables", []):
                            if t.get("name", "").lower() in r_str:
                                flds = {f.get("name", "").lower() for f in t.get("fields", [])}
                                if "deleted_at" in flds:
                                    has_deleted_at = True
                                    break
                        if not has_deleted_at:
                            continue
                    
                    valid_rules.append(rule)
                logic["rules"] = valid_rules

            logic["rules"] = sorted(logic["rules"], key=lambda x: x.get("name", ""))
            
        # Assemble
        config = {
            "intent": intent,
            "architecture": arch,
            "database": db,
            "api": api,
            "ui": ui,
            "auth": auth,
            "business_logic": logic
        }
        
        config_hash = generate_hash(config)
        
        final_config = {
            "metadata": {
                "app_name": intent.get("app_name", "Unknown"),
                "version": "1.0.0",
                "generated_at": datetime.utcnow().isoformat(),
                "mode": mode,
                "config_hash": config_hash,
                "trace_id": trace_id,
                "assumptions": intent.get("assumptions", []),
                "warnings": []
            },
            **config,
            "validation_report": {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "repair_attempts": 0
            },
            "repair_report": {
                "repair_attempted": False,
                "repair_rounds": 0,
                "repaired_layers": [],
                "unresolved_errors": [],
                "repair_log": []
            },
            "runtime_report": {
                "executable": False,
                "database_created": False,
                "tables_created": [],
                "api_routes_registered": [],
                "ui_routes_validated": [],
                "auth_rules_validated": False,
                "simulation_results": [],
                "errors": []
            },
            "pipeline_trace": pipeline_trace
        }
        
        return final_config
