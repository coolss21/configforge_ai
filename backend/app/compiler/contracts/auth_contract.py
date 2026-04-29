from pydantic import BaseModel
from typing import List

class AuthRole(BaseModel):
    name: str
    permissions: List[str]

class AccessRule(BaseModel):
    role: str
    resource: str
    actions: List[str]

class AuthSchema(BaseModel):
    auth_required: bool
    roles: List[AuthRole]
    access_rules: List[AccessRule]
