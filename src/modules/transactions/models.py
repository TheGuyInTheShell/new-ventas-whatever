from sqlalchemy import String, Integer, ForeignKey, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from core.database import BasicBaseAsync

if TYPE_CHECKING:
    from src.modules.users.models import User
    from src.modules.balances.models import Balance
    from src.modules.transactions.meta.models import MetaTransaction


class Transaction(BasicBaseAsync):
    __tablename__ = "transactions"
    
    quantity: Mapped[str] = mapped_column(String, nullable=True) # varchar in DBML
    operation_type: Mapped[str] = mapped_column(Enum("+", "-", name="operation_type_enum"), nullable=True)
    reference_code: Mapped[str] = mapped_column(String(100), nullable=True) # Nro Factura, Recibo
    
    quantity_to: Mapped[str] = mapped_column(String, nullable=True)
    # Foreign Keys
    ref_by_user: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    ref_balance_from: Mapped[int] = mapped_column(Integer, ForeignKey("balances.id"), nullable=False)
    ref_balance_to: Mapped[int] = mapped_column(Integer, ForeignKey("balances.id"), nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[ref_by_user]) # Assuming User model is available

    
    balance_from: Mapped["Balance"] = relationship("Balance", foreign_keys=[ref_balance_from])
    balance_to: Mapped["Balance"] = relationship("Balance", foreign_keys=[ref_balance_to])

    meta: Mapped[list["MetaTransaction"]] = relationship("MetaTransaction", back_populates="transaction")
    
    __table_args__ = (
        Index("uq_transactions_id", "id", unique=True),
        {"extend_existing": True},
    )
