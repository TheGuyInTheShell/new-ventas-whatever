from sqlalchemy import String, Integer, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import BaseAsync
from app.modules.values.models import Value


class MetaValue(BaseAsync):
    """
    Flexible key-value metadata for values.
    Examples: year, month, promotion, category, etc.
    """
    __tablename__ = "meta_values"

    ref_value: Mapped[int] = mapped_column(
        Integer, ForeignKey("values.id"), nullable=False
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Relationship back to Value
    value_obj: Mapped["Value"] = relationship("Value", back_populates="meta")

    __table_args__ = (
        Index("idx_values_meta_key_ref_value", "key", "ref_value", unique=True),
    )
