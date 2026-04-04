from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from core.database import BaseAsync

if TYPE_CHECKING:
    from app.modules.invoices.models import Invoice
    from app.modules.transactions.models import Transaction


class InvoiceTransaction(BaseAsync):
    __tablename__ = "invoice_transactions"

    ref_invoice: Mapped[int] = mapped_column(
        Integer, ForeignKey("invoices.id"), nullable=False
    )
    ref_transaction: Mapped[int] = mapped_column(
        Integer, ForeignKey("transactions.id"), nullable=False
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="invoice_transactions")
    transaction: Mapped["Transaction"] = relationship("Transaction")
