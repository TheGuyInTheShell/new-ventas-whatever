from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from core.database import RelationBaseAsync

if TYPE_CHECKING:
    from src.modules.invoices.models import Invoice
    from src.modules.business_entities.models import BusinessEntity


class InvoiceBusinessEntity(RelationBaseAsync):
    __tablename__ = "invoice_business_entities"

    ref_invoice: Mapped[int] = mapped_column(
        Integer, ForeignKey("invoices.id"), nullable=False
    , primary_key=True)
    ref_business_entity: Mapped[int] = mapped_column(
        Integer, ForeignKey("business_entities.id", ondelete="CASCADE"), nullable=False
    , primary_key=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="invoice_business_entities")
    business_entity: Mapped["BusinessEntity"] = relationship("BusinessEntity")
