from pydantic import BaseModel
from typing import List

class SimulationResult(BaseModel):
    operation: str
    success: bool
    message: str

class RuntimeReport(BaseModel):
    executable: bool
    database_created: bool
    tables_created: List[str]
    api_routes_registered: List[str]
    ui_routes_validated: List[str]
    auth_rules_validated: bool
    simulation_results: List[SimulationResult]
    errors: List[str]
