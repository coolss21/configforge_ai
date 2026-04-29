import json
import time
from app.core.llm_client import llm_client
from app.compiler.contracts.architecture_contract import ArchitectureIR

class SystemDesigner:
    async def run(self, intent_data: dict, mode: str) -> tuple[dict, int]:
        start_time = time.time()
        
        system_prompt = f"""
        Design the system architecture based on the following IntentIR data. Output strictly JSON matching the ArchitectureIR schema.
        Rules:
        - Every module must map to at least one feature.
        - Every user flow actor must exist as a role.
        - Every entity used by a module must exist in IntentIR.
        - Admin analytics must produce dashboard/data-flow requirements.
        - Premium gating must produce a subscription/payment flow.
        
        INTENT: {json.dumps(intent_data)}
        """
        
        temperature = 0.0 if mode == "quality" else 0.1
        result = await llm_client.generate_json(system_prompt, "ArchitectureIR", temperature)
        
        latency = int((time.time() - start_time) * 1000)
        return result, latency
