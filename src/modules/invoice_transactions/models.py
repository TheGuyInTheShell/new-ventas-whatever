from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from core.database import RelationBaseAsync

if TYPE_CHECKING:
    from src.modules.invoices.models import Invoice
    from src.modules.transactions.models import Transaction


class InvoiceTransaction(RelationBaseAsync):
    __tablename__ = "invoice_transactions"

    ref_invoice: Mapped[int] = mapped_column(
        Integer, ForeignKey("invoices.id"), nullable=False
    , primary_key=True)
    ref_transaction: Mapped[int] = mapped_column(
        Integer, ForeignKey("transactions.id"), nullable=False
    , primary_key=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="invoice_transactions")
    transaction: Mapped["Transaction"] = relationship("Transaction")
