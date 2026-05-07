from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from core.database import RelationBaseAsync

if TYPE_CHECKING:
    from src.modules.values.models import Value


class ValuesHierarchy(RelationBaseAsync):
    __tablename__ = "values_hierarchy"
    
    ref_value_top: Mapped[int] = mapped_column(
        Integer, ForeignKey("values.id"), nullable=False
    , primary_key=True)
    ref_value_bottom: Mapped[int] = mapped_column(
        Integer, ForeignKey("values.id"), nullable=False
    , primary_key=True)

    # Relationships
    value_top: Mapped["Value"] = relationship("Value", foreign_keys=[ref_value_top])
    value_bottom: Mapped["Value"] = relationship("Value", foreign_keys=[ref_value_bottom])
