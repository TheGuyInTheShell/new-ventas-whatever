from typing import TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import RelationBaseAsync

if TYPE_CHECKING:
    from src.modules.transactions_buffer.models import TransactionBuffer


class MetaTransactionBuffer(RelationBaseAsync):
    __tablename__ = "meta_transactions_buffer"

    key: Mapped[str] = mapped_column(String(100), primary_key=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    ref_transaction_buffer: Mapped[int] = mapped_column(
        ForeignKey("transactions_buffer.id"), nullable=False
    , primary_key=True)

    transaction_buffer: Mapped["TransactionBuffer"] = relationship(
        "TransactionBuffer", back_populates="meta"
    )

    __table_args__ = (
        Index(
            "idx_meta_tx_buffer_key_ref",
            "key", "ref_transaction_buffer",
            unique=True,
        ),
    )
