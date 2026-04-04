from typing import Optional, List
from pydantic import BaseModel


class RQInvoice(BaseModel):
    context: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    serial: Optional[str] = None
    notes: Optional[str] = None


class RSInvoice(BaseModel):
    uid: str
    id: int
    context: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    serial: Optional[str] = None
    notes: Optional[str] = None


class RSInvoiceList(BaseModel):
    data: list[RSInvoice] | List = []
    total: int = 0
    page: int | None = 0
    page_size: int | None = 0
    total_pages: int | None = 0
    has_next: bool | None = False
    has_prev: bool | None = False
    next_page: int | None = 0
    prev_page: int | None = 0


# --- Bulk endpoint schemas ---

class RQInvoiceBulkItem(BaseModel):
    """Single line-item within a bulk invoice request."""
    quantity: float      # amount given in the exchange
    quantity_to: float   # amount received in the exchange
    operation_type: str


class RQInvoiceBulk(BaseModel):
    """
    Complex request: create an invoice, link business entities,
    and register N transactions — all in one call.
    """
    # Invoice fields
    context: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    serial: Optional[str] = None
    notes: Optional[str] = None

    # Business entity links
    business_entity_ids: List[int] = []

    # Transaction context
    ref_by_user: int
    ref_balance_from: int
    ref_balance_to: int
    reference_code: Optional[str] = None

    # Line items
    items: List[RQInvoiceBulkItem]


class RQTransactionItemFull(BaseModel):
    """Single line-item within a bulk invoice request."""

    # Transaction context
    quantity: float
    quantity_to: float
    operation_type: str
    ref_by_user: int
    ref_balance_from: int
    ref_balance_to: int
    reference_code: Optional[str] = None
    business_entity_ids: List[int] = []

class RQInvoiceFullTransactionBulk(BaseModel):
    """
    Complex request: create an invoice, link business entities,
    and register N transactions — all in one call.
    """
    # Line items

    context: str
    name: str
    type: str
    serial: str
    notes: str

    items: List[RQTransactionItemFull]


class RSInvoiceBulkTransaction(BaseModel):
    uid: str
    id: int
    quantity: Optional[str] = None
    quantity_to: Optional[str] = None
    operation_type: Optional[str] = None
    reference_code: Optional[str] = None
    ref_balance_from: int
    ref_balance_to: int


class RSInvoiceBulk(BaseModel):
    invoice: RSInvoice
    transactions: List[RSInvoiceBulkTransaction]
    linked_business_entity_count: int
