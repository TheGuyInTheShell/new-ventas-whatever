from sqlalchemy import Float, ForeignKey, Index, Integer, String, text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from core.database import BasicBaseAsync

if TYPE_CHECKING:
    from src.modules.values.models import Value
    from src.modules.comparison_values.meta.models import MetaComparisonValue
    from src.modules.business_entities.models import BusinessEntity


class ComparisonValue(BasicBaseAsync):
    """
    Represents a comparison ratio between two values.
    Example: 1 USD = 46.5 VES (quantity_from=1, quantity_to=46.5)
    """

    __tablename__ = "comparation_values"

    ref_business_entity: Mapped[int] = mapped_column(
        Integer, ForeignKey("business_entities.id", ondelete="CASCADE"), nullable=False
    )

    quantity_from: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    quantity_to: Mapped[float] = mapped_column(Float, nullable=False)

    value_from: Mapped[int] = mapped_column(
        Integer, ForeignKey("values.id"), nullable=False
    )
    value_to: Mapped[int] = mapped_column(
        Integer, ForeignKey("values.id"), nullable=False
    )

    # Relationships
    source_value: Mapped["Value"] = relationship(
        "Value", foreign_keys=[value_from], back_populates="comparisons_from"
    )
    target_value: Mapped["Value"] = relationship(
        "Value", foreign_keys=[value_to], back_populates="comparisons_to"
    )

    meta: Mapped[list["MetaComparisonValue"]] = relationship(
        "MetaComparisonValue", back_populates="comparison_value"
    )

    business_entity: Mapped["BusinessEntity"] = relationship("BusinessEntity")

    __table_args__ = (
        Index("ix_comparation_values_ref_business_entity_active", "ref_business_entity"),
        Index("ix_comparation_values_value_from_active", "value_from", postgresql_where=(text("deleted_at IS NULL"))),
        Index("ix_comparation_values_value_to_active", "value_to", postgresql_where=(text("deleted_at IS NULL"))),
        Index("ix_comparison_values_value_to_ref_business_entity", "value_to", "ref_business_entity"),
        Index("ix_comparison_values_value_from_ref_business_entity", "value_from", "ref_business_entity"),
        UniqueConstraint(
            "value_from",
            "value_to",
            "ref_business_entity",
            name="uix_comparison_values_value_from_value_to",
        ),
    )
