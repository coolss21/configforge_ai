from pydantic import BaseModel
from typing import List, Literal, Any, Dict
from .intent_contract import IntentIR
from .architecture_contract import ArchitectureIR
from .db_contract import DBSchema
from .api_contract import APISchema
from .ui_contract import UISchema
from .auth_contract import AuthSchema
from .business_logic_contract import BusinessLogicSchema
from .validation_contract import ValidationReport
from .runtime_contract import RuntimeReport

class AppMetadata(BaseModel):
    app_name: str
    version: Literal["1.0.0"]
    generated_at: str
    mode: Literal["fast", "quality"]
    config_hash: str
    trace_id: str
    assumptions: List[str]
    warnings: List[str]

class RepairLogEntry(BaseModel):
    round: int
    layer: str
    error_codes: List[str]
    strategy: str
    success: bool

class RepairReport(BaseModel):
    repair_attempted: bool
    repair_rounds: int
    repaired_layers: List[str]
    unresolved_errors: List[Dict[str, Any]]
    repair_log: List[RepairLogEntry]

class StageTrace(BaseModel):
    stage: str
    status: Literal["success", "failed", "repaired", "skipped"]
    latency_ms: int
    repair_attempts: int
    notes: List[str]

class FinalAppConfig(BaseModel):
    metadata: AppMetadata
    intent: IntentIR
    architecture: ArchitectureIR
    database: DBSchema
    api: APISchema
    ui: UISchema
    auth: AuthSchema
    business_logic: BusinessLogicSchema
    validation_report: ValidationReport
    repair_report: RepairReport
    runtime_report: RuntimeReport
    pipeline_trace: List[StageTrace]
