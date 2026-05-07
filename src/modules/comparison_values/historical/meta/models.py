from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import RelationBaseAsync

if TYPE_CHECKING:
    from src.modules.comparison_values.historical.models import (
        ComparisonValueHistorical,
    )


class MetaComparisonValuesHistorical(RelationBaseAsync):
    __tablename__ = "meta_comparison_values_historical"
    key: Mapped[str] = mapped_column(String(100), primary_key=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    ref_comparison_value_historical: Mapped[int] = mapped_column(
        Integer, ForeignKey("comparation_values_historical.id"), nullable=False
    , primary_key=True)
    comparison_value_historical: Mapped["ComparisonValueHistorical"] = relationship(
        "ComparisonValueHistorical", foreign_keys=[ref_comparison_value_historical]
    )

    __table_args__ = (
        Index(
            "idx_meta_comp_val_hist_ref_comp_val_hist",
            "key",
            "ref_comparison_value_historical",
            unique=True,
        ),
    )
