from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from core.database import BasicBaseAsync

if TYPE_CHECKING:
    from src.modules.values.models import Value


class ValuesHierarchy(BasicBaseAsync):
    __tablename__ = "values_hierarchy"
    
    ref_value_top: Mapped[int] = mapped_column(
        Integer, ForeignKey("values.id"), nullable=False
    )
    ref_value_bottom: Mapped[int] = mapped_column(
        Integer, ForeignKey("values.id"), nullable=False
    )

    # Relationships
    value_top: Mapped["Value"] = relationship("Value", foreign_keys=[ref_value_top])
    value_bottom: Mapped["Value"] = relationship("Value", foreign_keys=[ref_value_bottom])
