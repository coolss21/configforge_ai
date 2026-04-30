import uuid
import time
import asyncio
from app.compiler.stages.intent_extractor import IntentExtractor
from app.compiler.stages.system_designer import SystemDesigner
from app.compiler.stages.schema_generator import SchemaGenerator
from app.compiler.stages.refinement_layer import RefinementLayer
from app.compiler.repair.repair_engine import RepairEngine
from app.compiler.runtime.executor import Executor
from app.core.utils import generate_hash

# Fix 8: module-level pipeline-wide result cache keyed by config_hash
_PIPELINE_CACHE: dict = {}



def parse_prompt_for_cache(prompt: str):
    lower_prompt = prompt.lower().strip()
    
    app_type = "CRM"
    if any(w in lower_prompt for w in ["inventory", "stock", "supplier"]):
        app_type = "Inventory"
    elif any(w in lower_prompt for w in ["student", "teacher", "course", "assignment"]):
        app_type = "LMS"
    elif any(w in lower_prompt for w in ["ticket", "helpdesk", "agent", "sla"]):
        app_type = "Helpdesk"
    elif any(w in lower_prompt for w in ["hospital", "clinic", "healthcare", "doctor", "patient"]):
        app_type = "Healthcare Booking"
    elif any(w in lower_prompt for w in ["booking", "appointment", "calendar", "service"]):
        app_type = "Booking"

    features = []
    if any(w in lower_prompt for w in ["payment", "payments", "checkout", "billing"]):
        features.append("payments")
    if any(w in lower_prompt for w in ["premium", "plan", "subscription", "membership"]):
        features.append("premium plan")
    if any(w in lower_prompt for w in ["analytics", "reports", "admin analytics"]):
        features.append("admin analytics")
        
    return lower_prompt, app_type, sorted(features)

class CompilerPipeline:
    def __init__(self):
        self.intent_extractor = IntentExtractor()
        self.system_designer  = SystemDesigner()
        self.schema_generator = SchemaGenerator()
        self.refinement_layer = RefinementLayer()
        self.repair_engine    = RepairEngine()
        self.runtime_executor = Executor()

    async def generate(self, prompt: str, mode: str) -> dict:
        trace_id     = str(uuid.uuid4())
        pipeline_trace = []

        # Fix 8: check cache by prompt hash
        lower_prompt, app_type, features = parse_prompt_for_cache(prompt)
        prompt_hash = generate_hash({"prompt": lower_prompt, "mode": mode, "app_type": app_type, "features": features})
        if prompt_hash in _PIPELINE_CACHE:
            cached = _PIPELINE_CACHE[prompt_hash]
            cached["trace_id"] = trace_id   # fresh trace id for each call
            cached["_from_cache"] = True
            return cached

        # ── Stage 1: Intent extraction ────────────────────────────────────────
        intent, lat1 = await self.intent_extractor.run(prompt, mode)
        
        # Inject metadata
        intent["input_prompt_hash"] = prompt_hash
        intent["app_type"] = app_type
        intent["features"] = list(set(intent.get("features", []) + features))
        intent["template_used"] = app_type.lower()
        intent["fallback_used"] = mode == "fast"
        
        pipeline_trace.append({
            "stage": "Intent Extraction", "status": "success",
            "latency_ms": lat1, "repair_attempts": 0, "notes": [f"Extracted features: {', '.join(intent['features'])}"]
        })

        # ── Stage 2: Architecture design ──────────────────────────────────────
        arch, lat2 = await self.system_designer.run(intent, mode)
        pipeline_trace.append({
            "stage": "System Design", "status": "success",
            "latency_ms": lat2, "repair_attempts": 0, "notes": []
        })

        # ── Stage 3: Schema generation (parallel in fast mode) ────────────────
        db, api, ui, auth, logic, lat3 = await self.schema_generator.run(
            intent, arch, mode
        )
        pipeline_trace.append({
            "stage": "Schema Generation", "status": "success",
            "latency_ms": lat3, "repair_attempts": 0, "notes": []
        })

        # ── Stage 4: Refinement + assembly (deterministic, no LLM) ───────────
        t4 = time.perf_counter()
        config = self.refinement_layer.run(
            intent, arch, db, api, ui, auth, logic, mode, trace_id, pipeline_trace
        )
        lat4 = int((time.perf_counter() - t4) * 1000)
        pipeline_trace.append({
            "stage": "Refinement", "status": "success",
            "latency_ms": lat4, "repair_attempts": 0, "notes": []
        })

        # ── Stage 5 & 6: Validation + deterministic repair ────────────────────
        t5 = time.perf_counter()
        config = await self.repair_engine.run(config, mode)
        lat5   = int((time.perf_counter() - t5) * 1000)

        val_report  = config.get("validation_report", {})
        rep_report  = config.get("repair_report", {})
        
        # Sync repair rounds into validation report
        val_report["repair_attempts"] = rep_report.get("repair_rounds", 0)
        pipeline_trace.append({
            "stage": "Validation & Repair",
            "status": "success" if val_report.get("is_valid") else "repaired"
                      if rep_report.get("repair_rounds", 0) > 0 else "failed",
            "latency_ms":     lat5,
            "repair_attempts": rep_report.get("repair_rounds", 0),
            "checks_count":   val_report.get("checks_count", 0),
            "error_count":    val_report.get("error_count", 0),
            "warning_count":  val_report.get("warning_count", 0),
            "validation_time_ms": val_report.get("validation_time_ms", 0),
            "notes": (
                [f"Repaired layers: {rep_report.get('repaired_layers')}"]
                if rep_report.get("repair_rounds", 0) > 0 else []
            )
        })

        # ── Stage 7: Runtime simulation ───────────────────────────────────────
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

        config["pipeline_trace"] = pipeline_trace

        result = {
            "success":           val_report.get("is_valid") and runtime_report["executable"],
            "trace_id":          trace_id,
            "config_hash":       config["metadata"]["config_hash"],
            "final_config":      config,
            "validation_report": val_report,
            "repair_report":     rep_report,
            "runtime_report":    runtime_report,
            "metrics": {
                "latency_ms":    sum(t["latency_ms"] for t in pipeline_trace),
                "repair_rounds": rep_report.get("repair_rounds", 0),
                "valid_json":    True,
                "schema_valid":  val_report.get("is_valid", False),
                "checks_count":  val_report.get("checks_count", 0),
                "error_count":   val_report.get("error_count", 0),
                "warning_count": val_report.get("warning_count", 0),
                "validation_time_ms": val_report.get("validation_time_ms", 0),
                "simulation_count": len(runtime_report.get("simulation_results", [])),
            },
            "_from_cache": False
        }

        _PIPELINE_CACHE[prompt_hash] = result
        return result
