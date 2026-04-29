from pydantic import BaseModel, Field
from typing import List, Literal

class EntityField(BaseModel):
    name: str
    type: Literal["string", "number", "boolean", "date", "datetime", "email", "enum", "currency"]
    required: bool
    description: str

class Entity(BaseModel):
    name: str
    description: str
    fields: List[EntityField]

class IntentIR(BaseModel):
    app_name: str
    app_type: str
    description: str
    primary_users: List[str]
    features: List[str]
    entities: List[Entity]
    roles: List[str]
    permissions: List[str]
    business_rules: List[str]
    integrations: List[str]
    ambiguities: List[str]
    assumptions: List[str]
