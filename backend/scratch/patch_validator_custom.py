content = open('app/compiler/validators/cross_layer_validator.py', encoding='utf-8').read()
addition = """

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

"""
new = content.replace('        return errors, checks\n', addition + '        return errors, checks\n', 1)
open('app/compiler/validators/cross_layer_validator.py', 'w', encoding='utf-8').write(new)
print('OK - lines:', new.count('\\n'))
