import sys

def patch_repair_engine():
    with open('app/compiler/repair/repair_engine.py', 'r') as f:
        content = f.read()

    normalization_logic = """
    def _normalize_intent(self, config: dict):
        intent = config.get("intent", {})
        if not isinstance(intent, dict):
            return

        # normalize_missing_required_metadata
        if not intent.get("app_name"): intent["app_name"] = "Generated App"
        if not intent.get("app_type"): intent["app_type"] = "Generic"
        if not intent.get("description"): intent["description"] = "Generated application."
        if not intent.get("primary_users"): intent["primary_users"] = ["user"]
        if not intent.get("features"): intent["features"] = []
        if not intent.get("permissions"): intent["permissions"] = ["read", "write"]
        if not intent.get("business_rules"): intent["business_rules"] = []
        if not intent.get("integrations"): intent["integrations"] = []
        if not intent.get("ambiguities"): intent["ambiguities"] = []
        if not intent.get("assumptions"): intent["assumptions"] = ["Assumed standard DB"]

        # normalize_intent_fields / normalize_entity_descriptions
        entities = intent.get("entities", [])
        if not isinstance(entities, list):
            return
            
        for e in entities:
            if not isinstance(e, dict): continue
            if not e.get("description"): e["description"] = f"Entity representing {e.get('name', 'item')}"
            
            fields = e.get("fields", [])
            if not isinstance(fields, list): continue
            
            for f in fields:
                if not isinstance(f, dict): continue
                if not f.get("name"): f["name"] = "unknown_field"
                if not f.get("type"): f["type"] = "string"
                if "required" not in f: f["required"] = False
                
                if not f.get("description"):
                    fn = f["name"].lower()
                    if fn == "id": desc = "Primary key"
                    elif fn == "name": desc = "Display name"
                    elif fn == "email": desc = "Email address"
                    elif fn == "created_at": desc = "Creation timestamp"
                    elif fn == "updated_at": desc = "Last update timestamp"
                    elif fn == "status": desc = "Current status"
                    elif fn == "amount": desc = "Payment amount"
                    elif fn == "provider": desc = "Payment provider"
                    elif fn == "user_id": desc = "Reference to user"
                    elif fn == "plan_id": desc = "Reference to plan"
                    elif fn == "started_at": desc = "Subscription start timestamp"
                    elif fn == "expires_at": desc = "Subscription expiry timestamp"
                    else: desc = f"Field for {fn}"
                    f["description"] = desc

"""
    
    if "def _normalize_intent(" not in content:
        # inject before _apply_repair
        content = content.replace("    # ── Strategy dispatcher ────────────────────────────────────────────────────", normalization_logic + "\n    # ── Strategy dispatcher ────────────────────────────────────────────────────")

    # In `run()`, before validator.validate(config):
    # We want to run normalizations before EVERY validation if possible, or at least before final validation.
    # The requirement says: "Before final validation, always run: normalize_intent_fields ..."
    # Let's run it at the very beginning of `run()` and inside the loop.
    
    inject_run = """        self._normalize_intent(config)
        validator   = MasterValidator()"""
    
    content = content.replace("        validator   = MasterValidator()", inject_run)

    with open('app/compiler/repair/repair_engine.py', 'w') as f:
        f.write(content)
    print("Patched repair engine")

if __name__ == "__main__":
    patch_repair_engine()
