from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import BaseAsync

if TYPE_CHECKING:
    from app.modules.comparison_values.models import ComparisonValue

class MetaComparisonValue(BaseAsync):
    __tablename__ = "meta_comparison_values"
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    ref_comparison_value: Mapped[int] = mapped_column(Integer, ForeignKey("comparation_values.id"), nullable=False)
    comparison_value: Mapped["ComparisonValue"] = relationship("ComparisonValue", foreign_keys=[ref_comparison_value])


    __table_args__ = (
        Index("idx_values_meta_ref_comparison_value", "key", "ref_comparison_value", unique=True),
    )
