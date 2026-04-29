from pydantic import BaseModel
from typing import List, Literal, Optional, Dict, Any

class APIEndpoint(BaseModel):
    path: str
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    entity: str
    operation: Literal["list", "create", "read", "update", "delete", "custom"]
    request_body: Optional[Dict[str, Any]] = None
    response_body: Dict[str, Any]
    required_role: Optional[str] = None
    validation: Dict[str, Any]

class APISchema(BaseModel):
    endpoints: List[APIEndpoint]
