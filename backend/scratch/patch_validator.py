import sys

def patch_validator():
    with open('app/compiler/validators/cross_layer_validator.py', 'r') as f:
        content = f.read()
        
    new_checks = """
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
        has_analytics_intent = any(w in f for f in features_lower for w in ["analytics"])
        
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
"""
    
    if "10. Empty UI Components" not in content:
        content = content.replace("        return errors, checks", new_checks + "\n        return errors, checks")
        with open('app/compiler/validators/cross_layer_validator.py', 'w') as f:
            f.write(content)
        print("Patched validator")

if __name__ == "__main__":
    patch_validator()
