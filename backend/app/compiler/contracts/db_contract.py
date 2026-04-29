from pydantic import BaseModel
from typing import List, Literal, Optional

class DBReference(BaseModel):
    table: str
    field: str

class DBField(BaseModel):
    name: str
    type: Literal["TEXT", "INTEGER", "REAL", "BOOLEAN", "DATE", "DATETIME"]
    primary_key: bool
    nullable: bool
    unique: bool
    references: Optional[DBReference] = None

class DBTable(BaseModel):
    name: str
    fields: List[DBField]

class DBSchema(BaseModel):
    tables: List[DBTable]
