from sqlalchemy import Integer, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import BaseAsync
from app.modules.values.models import Value

class ComparisonValueHistorical(BaseAsync):
    """
    Historical snapshot of comparison values for tracking changes over time.
    Same structure as ComparisonValue but for historical records.
    """
    __tablename__ = "comparation_values_historical"

    context: Mapped[str] = mapped_column(String, nullable=False)

    quantity_from: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    quantity_to: Mapped[float] = mapped_column(Float, nullable=False)
    
    value_from: Mapped[int] = mapped_column(
        Integer, ForeignKey("values.id"), nullable=False
    )
    value_to: Mapped[int] = mapped_column(
        Integer, ForeignKey("values.id"), nullable=False
    )
    
    # Reference to the original comparison (optional)
    original_comparison_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("comparation_values.id"), nullable=True
    )