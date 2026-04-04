from typing import Optional, Literal, List
from pydantic import BaseModel

class RQTransaction(BaseModel):
    quantity: str
    operation_type: Literal["+", "-"]
    reference_code: Optional[str] = None
    
    ref_by_user: int
    ref_value_from: int
    ref_value_to: int
    ref_business_entity_from: int
    ref_business_entity_to: int
    ref_balance_from: int
    ref_balance_to: int
    ref_comparation_values_historical: int


class RQSaleItem(BaseModel):
    value_id: int
    quantity: float


class RQSale(BaseModel):
    items: List[RQSaleItem]
    ref_by_user: int
    ref_business_entity_from: int
    ref_business_entity_to: int
    ref_balance_from: int # Inventory/Stock balance
    ref_balance_to: int # Cash/Bank balance
    currency_id: int
    reference_code: Optional[str] = None


class RSTransaction(BaseModel):
    uid: str
    id: int
    quantity: Optional[str] = None
    operation_type: Optional[str] = None
    reference_code: Optional[str] = None
    
    ref_by_user: int
    ref_value_from: int
    ref_value_to: int
    ref_business_entity_from: int
    ref_business_entity_to: int
    ref_balance_from: int
    ref_balance_to: int
    ref_comparation_values_historical: int


class RSTransactionList(BaseModel):
    data: List[RSTransaction]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_page: int
    prev_page: int
