from pydantic import BaseModel
from typing import List

class BusinessRule(BaseModel):
    name: str
    description: str
    trigger: str
    condition: str
    action: str
    entities_used: List[str]
    roles_affected: List[str]

class BusinessLogicSchema(BaseModel):
    rules: List[BusinessRule]
