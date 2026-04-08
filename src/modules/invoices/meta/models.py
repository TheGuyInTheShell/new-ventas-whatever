from typing import TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import BaseAsync

if TYPE_CHECKING:
    from src.modules.invoices.models import Invoice


class MetaInvoice(BaseAsync):
    __tablename__ = "meta_invoices"

    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    ref_invoice: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="meta")

    __table_args__ = (
        Index("idx_meta_invoices_key_ref", "key", "ref_invoice", unique=True),
    )
