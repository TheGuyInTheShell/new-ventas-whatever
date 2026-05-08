from sqlalchemy import ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Any, Optional

from core.database import RelationBaseAsync

if TYPE_CHECKING:
    from src.modules.comparison_values.models import ComparisonValue
    from src.modules.comparison_values.historical.models import (
        ComparisonValueHistorical,
    )


class ComparisonValueDecorator(RelationBaseAsync):
    """
    Decorators for active comparison values relationships.
    """

    __tablename__ = "decorators_comparation_values"

    ref_comparation_values_from: Mapped[int] = mapped_column(
        Integer, ForeignKey("comparation_values.id"), nullable=False, primary_key=True
    )
    ref_comparation_values_to: Mapped[int] = mapped_column(
        Integer, ForeignKey("comparation_values.id"), nullable=False, primary_key=True
    )

    comparison_decorators: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )

    # Relationships
    source_comparison: Mapped["ComparisonValue"] = relationship(
        "ComparisonValue", foreign_keys=[ref_comparation_values_from]
    )
    target_comparison: Mapped["ComparisonValue"] = relationship(
        "ComparisonValue", foreign_keys=[ref_comparation_values_to]
    )


class ComparisonValueDecoratorHistorical(RelationBaseAsync):
    """
    Decorators for historical comparison values relationships.
    """

    __tablename__ = "decorators_comparation_values_historical"

    ref_comparation_values_from: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("comparation_values_historical.id"),
        nullable=False,
        primary_key=True,
    )
    ref_comparation_values_to: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("comparation_values_historical.id"),
        nullable=False,
        primary_key=True,
    )

    comparison_decorators: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )

    # Relationships
    source_comparison: Mapped["ComparisonValueHistorical"] = relationship(
        "ComparisonValueHistorical", foreign_keys=[ref_comparation_values_from]
    )
    target_comparison: Mapped["ComparisonValueHistorical"] = relationship(
        "ComparisonValueHistorical", foreign_keys=[ref_comparation_values_to]
    )
