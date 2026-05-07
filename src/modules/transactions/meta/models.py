from typing import TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import RelationBaseAsync

if TYPE_CHECKING:
    from src.modules.transactions.models import Transaction


class MetaTransaction(RelationBaseAsync):
    __tablename__ = "meta_transactions"
    key: Mapped[str] = mapped_column(String(100), primary_key=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    ref_transaction: Mapped[int] = mapped_column(ForeignKey("transactions.id"), nullable=False, primary_key=True)
    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="meta")


    __table_args__ = (
        Index("idx_values_meta_key_ref_transaction", "key", "ref_transaction", unique=True),
    )