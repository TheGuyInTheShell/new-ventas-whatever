from sqlalchemy import String, Integer, ForeignKey, Enum, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from core.database import BasicBaseAsync

if TYPE_CHECKING:
    from src.modules.users.models import User
    from src.modules.balances.models import Balance
    from src.modules.transactions_buffer.meta.models import MetaTransactionBuffer


class TransactionBuffer(BasicBaseAsync):
    __tablename__ = "transactions_buffer"

    quantity: Mapped[str] = mapped_column(String, nullable=True)
    operation_type: Mapped[str] = mapped_column(
        Enum("+", "-", name="buffer_operation_type_enum"), nullable=True
    )
    state: Mapped[str] = mapped_column(String(50), nullable=True)
    trigger: Mapped[str] = mapped_column(String(100), nullable=True)

    # Self-referencing FK for inverse transaction
    ref_inverse_transaction: Mapped[int] = mapped_column(
        Integer, ForeignKey("transactions_buffer.id", use_alter=True, name="fk_transactions_buffer_inverse"),
        nullable=False
    )

    # Foreign Keys
    ref_by_user: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    ref_balance_from: Mapped[int] = mapped_column(
        Integer, ForeignKey("balances.id"), nullable=False
    )
    ref_balance_to: Mapped[int] = mapped_column(
        Integer, ForeignKey("balances.id"), nullable=False
    )

    # Relationships
    inverse_transaction: Mapped["TransactionBuffer"] = relationship(
        "TransactionBuffer",
        foreign_keys=[ref_inverse_transaction],
    )
    user: Mapped["User"] = relationship("User", foreign_keys=[ref_by_user])

    balance_from: Mapped["Balance"] = relationship("Balance", foreign_keys=[ref_balance_from])
    balance_to: Mapped["Balance"] = relationship("Balance", foreign_keys=[ref_balance_to])

    meta: Mapped[list["MetaTransactionBuffer"]] = relationship(
        "MetaTransactionBuffer", back_populates="transaction_buffer"
    )

    __table_args__ = (
        Index("uq_transactions_buffer_id", "id", unique=True),
        Index("ix_transactions_buffer_ref_by_user_active", "ref_by_user", postgresql_where=(text("deleted_at IS NULL"))),
        Index("ix_transactions_buffer_ref_balance_from_active", "ref_balance_from", postgresql_where=(text("deleted_at IS NULL"))),
        Index("ix_transactions_buffer_ref_balance_to_active", "ref_balance_to", postgresql_where=(text("deleted_at IS NULL"))),
        Index("ix_transactions_buffer_state_active", "state", postgresql_where=(text("deleted_at IS NULL"))),
        {"extend_existing": True},
    )
