from pydantic import BaseModel
from typing import List, Literal, Optional

class UIComponent(BaseModel):
    type: Literal["form", "table", "chart", "card", "button", "nav", "text"]
    entity: Optional[str] = None
    api_endpoint: Optional[str] = None
    fields: List[str]
    actions: List[str]

class UIPage(BaseModel):
    name: str
    route: str
    required_role: Optional[str] = None
    layout: Literal["dashboard", "form", "table", "detail", "auth", "landing"]
    components: List[UIComponent]

class UISchema(BaseModel):
    pages: List[UIPage]
