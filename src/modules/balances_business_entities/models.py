from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from core.database import BaseAsync

if TYPE_CHECKING:
    from app.modules.business_entities.models import BusinessEntity
    from app.modules.balances.models import Balance


class BalanceBusinessEntity(BaseAsync):
    __tablename__ = "balances_business_entities"

    ref_business_entity: Mapped[int] = mapped_column(
        Integer, ForeignKey("business_entities.id"), nullable=False
    )
    ref_balance: Mapped[int] = mapped_column(
        Integer, ForeignKey("balances.id"), nullable=False
    )

    # Relationships
    business_entity: Mapped["BusinessEntity"] = relationship("BusinessEntity")
    balance: Mapped["Balance"] = relationship("Balance")
