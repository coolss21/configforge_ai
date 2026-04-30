def normalize_intent(intent: dict, prompt: str) -> dict:
    lower_prompt = prompt.lower()
    
    # Defaults
    if "requested_feature_flags" not in intent:
        intent["requested_feature_flags"] = {}
        
    flags = intent["requested_feature_flags"]
    
    # 6. Sensitive Domain Handling
    sensitive_keywords = ["banking", "bank", "finance", "financial", "healthcare", "hospital", "medical", "insurance", "education"]
    if any(k in lower_prompt for k in sensitive_keywords) or flags.get("sensitive_domain", False):
        flags["sensitive_domain"] = True
        flags["auth"] = True
        
        assumptions = intent.get("assumptions", [])
        if "Auth enforced due to sensitive domain" not in assumptions:
            assumptions.append("Auth enforced due to sensitive domain")
        intent["assumptions"] = assumptions

    # Ensure flags are booleans
    for k in ["auth", "payments", "premium", "subscriptions", "analytics", "admin_dashboard", "sensitive_domain"]:
        flags[k] = bool(flags.get(k, False))
        
    if "auth" in lower_prompt or "login" in lower_prompt or "register" in lower_prompt or "users" in lower_prompt:
        flags["auth"] = True
        
    # Roles
    roles = intent.get("roles", [])
    if flags.get("auth") and "user" not in roles:
        roles.append("user")
    if (flags.get("admin_dashboard") or "admin" in lower_prompt) and "admin" not in roles:
        roles.append("admin")
    intent["roles"] = roles
    
    # Entities normalization
    seen_entities = set()
    unique_entities = []
    
    default_descriptions = {
        "id": "Primary key",
        "name": "Display name",
        "email": "Email address",
        "title": "Title",
        "description": "Description",
        "created_at": "Creation timestamp",
        "updated_at": "Last update timestamp",
        "status": "Current status",
        "role": "User role",
        "password_hash": "Hashed password",
        "amount": "Payment amount",
        "provider": "Payment provider",
        "user_id": "Reference to user",
        "customer_id": "Reference to customer",
        "student_id": "Reference to student",
        "teacher_id": "Reference to teacher",
        "doctor_id": "Reference to doctor",
        "patient_id": "Reference to patient",
        "account_id": "Reference to account"
    }

    for ent in intent.get("entities", []):
        name = ent.get("name", "").lower().strip()
        if not name or name in seen_entities:
            continue
            
        seen_entities.add(name)
        if not ent.get("description"):
            ent["description"] = f"{name.capitalize()} record"
            
        for f in ent.get("fields", []):
            fname = f.get("name", "").lower()
            if not f.get("description"):
                if fname in default_descriptions:
                    f["description"] = default_descriptions[fname]
                else:
                    f["description"] = f"Field for {fname}"
        
        unique_entities.append(ent)
        
    intent["entities"] = unique_entities
    
    return intent
