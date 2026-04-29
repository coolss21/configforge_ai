class LogicalValidator:
    """
    Checks *logical* consistency within a single layer or across time
    (e.g. runtime state). Cross-layer structural checks live in
    CrossLayerValidator to avoid duplicate errors.
    """

    def validate(self, config: dict) -> tuple[list, list]:
        errors   = []
        warnings = []

        intent  = config.get("intent", {})
        auth    = config.get("auth", {})
        runtime = config.get("runtime_report", {})

        prompt_text = (
            intent.get("description", "").lower()
            + " "
            + " ".join(intent.get("features", [])).lower()
        )

        # ── auth_required must be true when login/auth is mentioned ──────────
        if ("login" in prompt_text or "auth" in prompt_text):
            if not auth.get("auth_required", False):
                errors.append({
                    "code":            "LOGIC_AUTH_MISSING",
                    "severity":        "high",
                    "layer":           "logical",
                    "message":         "Prompt references login/auth but auth_required is false.",
                    "repair_strategy": "set_auth_required_true",
                    "context":         {}
                })

        # ── Fix 2c: auth_rules_validated=false must block executable=true ─────
        # (auth_rules_validated lives on the auth layer; executable on runtime)
        if not auth.get("auth_rules_validated", True) and runtime.get("executable", False):
            errors.append({
                "code":    "EXEC_WITHOUT_AUTH_VALIDATION",
                "severity":"high",
                "layer":   "logical",
                "message": (
                    "runtime_report.executable is true but auth.auth_rules_validated "
                    "is false. Execution must be blocked until auth rules pass."
                ),
                "repair_strategy": "block_execution",
                "context": {}
            })

        # ── Logical conflict: public anonymous + admin-only ───────────────────
        if "anonymous" in prompt_text and "admin login" in prompt_text:
            warnings.append(
                "Conflict detected: Prompt asks for public anonymous access but also "
                "admin login. Assuming public landing page and protected admin dashboard."
            )

        return errors, warnings
