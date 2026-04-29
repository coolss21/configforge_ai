import time
from .cross_layer_validator import CrossLayerValidator
from .logical_validator import LogicalValidator
from .pydantic_validator import PydanticValidator


class MasterValidator:
    def validate(self, config: dict) -> dict:
        start    = time.perf_counter()
        errors   = []
        warnings = []
        checks   = 0

        # ── 1. Pydantic structural check ──────────────────────────────────────
        p_errors = PydanticValidator().validate(config)
        checks  += 1          # counts as one check pass
        errors.extend(p_errors)

        # ── 2. Cross-layer checks ─────────────────────────────────────────────
        # CrossLayerValidator.validate() returns (errors_list, checks_run_int)
        cl_result = CrossLayerValidator().validate(config)
        cl_errors, cl_checks = cl_result
        checks  += cl_checks
        errors.extend(cl_errors)

        # ── 3. Logical consistency checks ─────────────────────────────────────
        l_errors, l_warnings = LogicalValidator().validate(config)
        checks  += 1 + len(l_errors) + len(l_warnings)
        errors.extend(l_errors)
        warnings.extend(l_warnings)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 3)

        return {
            "is_valid":           len(errors) == 0,
            "errors":             errors,
            "warnings":           warnings,
            "checks_count":       checks,
            "error_count":        len(errors),
            "warning_count":      len(warnings),
            "validation_time_ms": elapsed_ms,
            "repair_attempts":    config.get("validation_report", {}).get("repair_attempts", 0),
        }
