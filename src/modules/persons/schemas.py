from typing import Optional, List
from pydantic import BaseModel
from src.modules.business_entities.schemas import RSBusinessEntity

class RQPerson(BaseModel):
    first_names: str
    last_names: str
    email: Optional[str] = None
    identifier: Optional[str] = None
    type_identifier: Optional[str] = None
    ref_business_entity: int


class RSPerson(BaseModel):
    uid: str
    id: int
    first_names: str
    last_names: str
    email: Optional[str] = None
    identifier: Optional[str] = None
    type_identifier: Optional[str] = None
    ref_business_entity: int
    # business_entity: Optional[RSBusinessEntity] = None # Optional expansion

class RSPersonList(BaseModel):
    data: list[RSPerson] | List = []
    total: int = 0
    page: int | None = 0
    page_size: int | None = 0
    total_pages: int | None = 0
    has_next: bool | None = False
    has_prev: bool | None = False
    next_page: int | None = 0
    prev_page: int | None = 0
