from typing import Optional, List, Literal
from pydantic import BaseModel, field_validator

class Transaction(BaseModel):
    quantity: float
    operation_type: Literal["+", "-"]
    reference_code: Optional[str] = None
    is_super_value: bool = False

    ref_value_from: int
    ref_value_to: int
    
    # We might need to resolve balances from these or provide them directly
    ref_balance_from: Optional[int] = None
    ref_balance_to: Optional[int] = None
    
    ref_comparation_values_historical: Optional[int] = None

    # meta_transaction remains as a list of dicts for extra data
    meta_transaction: List[dict] = []

class WrapSuperValue(BaseModel): # this model represents a field meta_value that a value can be composed of others and be a complex value, like ingredient -> dish has (ingredient 1, ingredient 2, ingredient 3). 
    id: int
    qty: float

class InvoiceSales(BaseModel):
    context: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    serial: Optional[str] = None
    notes: Optional[str] = None
    business_entity_id: int

    meta_invoice: List[dict] = []
    transactions: List[Transaction]

class RQAdjustBalance(BaseModel):
    balance_id: int # The inventory item (Value.id)
    new_quantity: float
    is_adjustment: bool
    notes: Optional[str] = None

    @field_validator('new_quantity')
    @classmethod
    def round_quantity(cls, v: float) -> float:
        return round(v, 4)
