from pydantic import BaseModel
from typing import List, Literal

class ValidationErrorItem(BaseModel):
    code: str
    severity: Literal["low", "medium", "high", "critical"]
    layer: Literal["intent", "architecture", "database", "api", "ui", "auth", "business_logic", "cross_layer", "runtime"]
    message: str
    repair_strategy: str

class ValidationReport(BaseModel):
    is_valid: bool
    errors: List[ValidationErrorItem]
    warnings: List[str]
    repair_attempts: int
