from pydantic import BaseModel
from typing import List

class Module(BaseModel):
    name: str
    responsibility: str
    entities_used: List[str]

class UserFlow(BaseModel):
    name: str
    actor: str
    steps: List[str]

class DataFlow(BaseModel):
    source: str
    target: str
    description: str

class Role(BaseModel):
    name: str
    description: str

class RoleModel(BaseModel):
    roles: List[Role]

class ArchitectureIR(BaseModel):
    app_name: str
    modules: List[Module]
    user_flows: List[UserFlow]
    data_flows: List[DataFlow]
    role_model: RoleModel
