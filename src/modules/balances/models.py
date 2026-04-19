from sqlalchemy import String, Integer, ForeignKey, Float, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from core.database import BasicBaseAsync

if TYPE_CHECKING:
    from src.modules.values.models import Value


class Balance(BasicBaseAsync):
    __tablename__ = "balances"

    type: Mapped[str] = mapped_column(String, nullable=False)

    quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    ref_value: Mapped[int] = mapped_column(
        Integer, ForeignKey("values.id"), nullable=False
    )

    value: Mapped["Value"] = relationship("Value", back_populates="balances")

    __table_args__ = (
        Index("ix_balances_ref_value_active", "ref_value", postgresql_where=(text("deleted_at IS NULL"))),
        Index("ix_balances_type_active", "type", postgresql_where=(text("deleted_at IS NULL"))),
        {"extend_existing": True},
    )
