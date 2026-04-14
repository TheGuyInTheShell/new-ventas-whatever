from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from core.database import BasicBaseAsync

if TYPE_CHECKING:
    from src.modules.invoices.meta.models import MetaInvoice
    from src.modules.invoice_transactions.models import InvoiceTransaction
    from src.modules.invoice_business_entities.models import InvoiceBusinessEntity


class Invoice(BasicBaseAsync):
    __tablename__ = "invoices"

    context: Mapped[str] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=True)
    type: Mapped[str] = mapped_column(String(100), nullable=True)
    serial: Mapped[str] = mapped_column(String(100), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    

    # Relationships
    meta: Mapped[list["MetaInvoice"]] = relationship("MetaInvoice", back_populates="invoice")
    invoice_transactions: Mapped[list["InvoiceTransaction"]] = relationship(
        "InvoiceTransaction", back_populates="invoice"
    )
    invoice_business_entities: Mapped[list["InvoiceBusinessEntity"]] = relationship(
        "InvoiceBusinessEntity", back_populates="invoice"
    )
