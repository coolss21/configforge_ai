import uuid
import time
from app.compiler.stages.intent_router import IntentRouter
from app.compiler.stages.intent_normalization import normalize_intent
from app.compiler.stages.schema_compiler import compile_schemas
from app.compiler.feature_modules.expansion import expand_features
from app.compiler.repair.repair_engine import RepairEngine
from app.compiler.runtime.executor import Executor
from app.core.utils import generate_hash

# 10. Cache Safety
_PIPELINE_CACHE: dict = {}

class CompilerPipeline:
    def __init__(self):
        self.intent_router = IntentRouter()
        self.repair_engine = RepairEngine()
        self.runtime_executor = Executor()

    async def generate(self, prompt: str, mode: str) -> dict:
        trace_id = str(uuid.uuid4())
        pipeline_trace = []

        # Cache key must include normalized prompt text, mode, etc.
        prompt_hash = generate_hash({"prompt": prompt.lower().strip(), "mode": mode})
        if prompt_hash in _PIPELINE_CACHE:
            cached = _PIPELINE_CACHE[prompt_hash]
            cached["trace_id"] = trace_id
            cached["_from_cache"] = True
            return cached

        # ── Stage 1 & 2: Prompt Intake & LLM Intent Router ────────────────────
        intent, lat1 = await self.intent_router.run(prompt, mode)
        intent["input_prompt_hash"] = prompt_hash
        
        # In case OpenRouter fails, fallback handling would go here, 
        # but IntentRouter always returns a JSON. If not, it returns empty dict.
        if not intent:
            intent = {"app_name": "Fallback App", "fallback_used": True}
        
        pipeline_trace.append({
            "stage": "Intent Router", "status": "success",
            "latency_ms": lat1, "repair_attempts": 0, "notes": ["Extracted IntentIR via LLM"]
        })

        # ── Stage 3: IntentIR Normalization ───────────────────────────────────
        t2 = time.perf_counter()
        intent = normalize_intent(intent, prompt)
        lat2 = int((time.perf_counter() - t2) * 1000)
        pipeline_trace.append({
            "stage": "Intent Normalization", "status": "success",
            "latency_ms": lat2, "repair_attempts": 0, "notes": ["Normalized and enforced domain rules"]
        })

        # ── Stage 4: Deterministic Schema Compiler ────────────────────────────
        t3 = time.perf_counter()
        db, api, ui, auth, logic = compile_schemas(intent)
        lat3 = int((time.perf_counter() - t3) * 1000)
        pipeline_trace.append({
            "stage": "Schema Compiler", "status": "success",
            "latency_ms": lat3, "repair_attempts": 0, "notes": ["Generated baseline schemas deterministically"]
        })

        # ── Stage 5: Feature Module Expansion ─────────────────────────────────
        t4 = time.perf_counter()
        expand_features(intent, db, api, ui, auth, logic)
        lat4 = int((time.perf_counter() - t4) * 1000)
        pipeline_trace.append({
            "stage": "Feature Expansion", "status": "success",
            "latency_ms": lat4, "repair_attempts": 0, "notes": ["Injected feature modules"]
        })

        # Combine into config
        config = {
            "metadata": {
                "app_name": intent.get("app_name", "App"),
                "mode": mode,
                "config_hash": generate_hash(intent)
            },
            "intent": intent,
            "database": db,
            "api": api,
            "ui": ui,
            "auth": auth,
            "business_logic": logic
        }

        # ── Stage 6 & 7: Validation + Targeted Repair ─────────────────────────
        t5 = time.perf_counter()
        config = await self.repair_engine.run(config, mode)
        lat5 = int((time.perf_counter() - t5) * 1000)

        val_report = config.get("validation_report", {})
        rep_report = config.get("repair_report", {})
        val_report["repair_attempts"] = rep_report.get("repair_rounds", 0)

        pipeline_trace.append({
            "stage": "Validation & Repair",
            "status": "success" if val_report.get("is_valid") else "repaired" if rep_report.get("repair_rounds", 0) > 0 else "failed",
            "latency_ms": lat5,
            "repair_attempts": rep_report.get("repair_rounds", 0),
            "checks_count": val_report.get("checks_count", 0),
            "error_count": val_report.get("error_count", 0),
            "notes": [f"Repaired layers: {rep_report.get('repaired_layers')}"] if rep_report.get("repair_rounds", 0) > 0 else []
        })

        # ── Stage 8: Runtime Simulation ───────────────────────────────────────
        t6 = time.perf_counter()
        runtime_report = self.runtime_executor.execute(config)
        config["runtime_report"] = runtime_report
        lat6 = int((time.perf_counter() - t6) * 1000)
        
        pipeline_trace.append({
            "stage": "Runtime Execution",
            "status": "success" if runtime_report["executable"] else "failed",
            "latency_ms": lat6, "repair_attempts": 0,
            "notes": runtime_report.get("errors", [])
        })

        # ── Stage 9: Final App Config ─────────────────────────────────────────
        config["pipeline_trace"] = pipeline_trace

        result = {
            "success": val_report.get("is_valid") and runtime_report["executable"],
            "trace_id": trace_id,
            "config_hash": config["metadata"]["config_hash"],
            "final_config": config,
            "validation_report": val_report,
            "repair_report": rep_report,
            "runtime_report": runtime_report,
            "metrics": {
                "latency_ms": sum(t["latency_ms"] for t in pipeline_trace),
                "repair_rounds": rep_report.get("repair_rounds", 0),
                "valid_json": True,
                "schema_valid": val_report.get("is_valid", False),
                "checks_count": val_report.get("checks_count", 0),
                "simulation_count": len(runtime_report.get("simulation_results", []))
            },
            "_from_cache": False
        }

        if val_report.get("is_valid") and runtime_report["executable"]:
            _PIPELINE_CACHE[prompt_hash] = result

        return result
