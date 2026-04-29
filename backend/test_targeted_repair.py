import asyncio
import json
from app.compiler.repair.repair_engine import RepairEngine
from app.compiler.validators.master_validator import MasterValidator

async def test_targeted_repair():
    config = {
        "metadata": {"config_hash": "testhash"},
        "intent": {
            "entities": [{"name": "contact", "fields": [{"name": "id"}, {"name": "name"}]}],
            "roles": ["admin", "user"]
        },
        "database": {
            "tables": [
                {"name": "contact", "fields": [{"name": "id", "type": "INT", "primary_key": True}]}
            ]
        },
        "api": {
            "endpoints": [
                {"path": "/api/users", "entity": "user", "required_role": "admin"}
            ]
        },
        "ui": {
            "pages": [
                {"route": "/dashboard", "required_role": "superuser", "components": [{"entity": "missing_entity", "api_endpoint": "/api/missing"}]}
            ]
        },
        "auth": {
            "roles": [{"name": "user"}],
            "auth_required": True,
            "access_rules": []
        },
        "business_logic": {}
    }

    print("--- Initial Validation ---")
    validator = MasterValidator()
    report = validator.validate(config)
    print(f"Is Valid: {report['is_valid']}")
    for err in report['errors']:
        print(f"Error: {err['message']} (Strategy: {err.get('repair_strategy')})")

    print("\n--- Running Repair Engine ---")
    engine = RepairEngine()
    repaired_config = await engine.run(config, "fast")
    
    print("\n--- Repair Report ---")
    rr = repaired_config.get("repair_report", {})
    print(json.dumps(rr, indent=2))

    print("\n--- Final Validation ---")
    final_report = validator.validate(repaired_config)
    print(f"Is Valid: {final_report['is_valid']}")
    if not final_report['is_valid']:
        for err in final_report['errors']:
            print(f"Error: {err['message']}")

if __name__ == "__main__":
    asyncio.run(test_targeted_repair())
