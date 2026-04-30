import sys

def patch_validator():
    with open('app/compiler/validators/cross_layer_validator.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    new_checks = """
        # ════════════════════════════════════════════════════════
        # 14. Prompt Coverage (TEMPLATE_PROMPT_MISMATCH)
        # ════════════════════════════════════════════════════════
        checks += 1
        app_type = intent.get("app_type", "")
        template_used = intent.get("template_used", "")
        app_name = intent.get("app_name", "")
        
        is_banking = "banking" in app_type.lower() or "finance" in app_type.lower() or "financial" in app_type.lower()
        
        if is_banking:
            if template_used not in ["banking", "finance"]:
                errors.append({
                    "code": "TEMPLATE_APP_TYPE_MISMATCH",
                    "severity": "high", "layer": "cross_layer",
                    "message": f"App type is {app_type} but template is {template_used}.",
                    "repair_strategy": "fix_template_mismatch",
                    "context": {}
                })
            
            missing_tables = []
            for req in ["users", "accounts", "transactions", "transfers", "audit_logs"]:
                if req not in all_tables:
                    missing_tables.append(req)
                    
            if missing_tables:
                errors.append({
                    "code": "TEMPLATE_PROMPT_MISMATCH",
                    "severity": "high", "layer": "cross_layer",
                    "message": f"Banking app missing tables: {missing_tables}",
                    "repair_strategy": "fix_template_mismatch",
                    "context": {}
                })
                
            if not auth.get("auth_required"):
                errors.append({
                    "code": "TEMPLATE_PROMPT_MISMATCH",
                    "severity": "high", "layer": "cross_layer",
                    "message": "Banking app must have auth_required=True.",
                    "repair_strategy": "set_auth_required_true",
                    "context": {}
                })
        
        # Check Job Board mismatch
        if "job board" in app_name.lower() and "job board" not in app_type.lower():
            errors.append({
                "code": "TEMPLATE_APP_TYPE_MISMATCH",
                "severity": "high", "layer": "cross_layer",
                "message": f"App name is {app_name} but app type is {app_type}.",
                "repair_strategy": "fix_template_mismatch",
                "context": {}
            })
"""
    
    if "14. Prompt Coverage" not in content:
        content = content.replace("        return errors, checks", new_checks + "\n        return errors, checks")
        with open('app/compiler/validators/cross_layer_validator.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Patched validator")

if __name__ == "__main__":
    patch_validator()
