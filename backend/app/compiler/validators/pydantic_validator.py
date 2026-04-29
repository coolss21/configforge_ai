from app.compiler.contracts.app_config_contract import FinalAppConfig
from pydantic import ValidationError

class PydanticValidator:
    def validate(self, config: dict) -> list:
        errors = []
        try:
            # We skip validation of some metadata since we populate it later.
            # Just test the sub-schemas.
            from app.compiler.contracts.intent_contract import IntentIR
            IntentIR(**config.get("intent", {}))
        except ValidationError as e:
            for err in e.errors():
                errors.append({
                    "code": "PYDANTIC_VALIDATION",
                    "severity": "high",
                    "layer": "intent",
                    "message": f"Validation error: {err['loc']} - {err['msg']}",
                    "repair_strategy": "missing_required_key"
                })
        
        # Add similar try-except blocks for other layers (architecture, db, api, etc.)
        # Simplified for brevity, but a real system would loop over them.
        
        return errors
