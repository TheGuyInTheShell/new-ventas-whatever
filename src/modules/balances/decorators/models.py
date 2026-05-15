from sqlalchemy import ForeignKey, Integer, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Any, Optional

from core.database import RelationBaseAsync

if TYPE_CHECKING:
    from src.modules.balances.models import Balance


class BalanceDecorator(RelationBaseAsync):
    """
    Decorators for active balances relationships.
    """

    __tablename__ = "decorators_balances"

    ref_balance_from: Mapped[int] = mapped_column(
        Integer, ForeignKey("balances.id"), nullable=False, primary_key=True
    )
    ref_balance_to: Mapped[int] = mapped_column(
        Integer, ForeignKey("balances.id"), nullable=False, primary_key=True
    )

    balance_decorators: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )

    is_reactive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    source_balance: Mapped["Balance"] = relationship(
        "Balance", foreign_keys=[ref_balance_from]
    )
    target_balance: Mapped["Balance"] = relationship(
        "Balance", foreign_keys=[ref_balance_to]
    )
