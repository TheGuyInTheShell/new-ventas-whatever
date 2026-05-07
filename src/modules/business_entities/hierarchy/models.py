from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from core.database import RelationBaseAsync

if TYPE_CHECKING:
    from src.modules.business_entities.models import BusinessEntity


class BusinessEntitiesHierarchy(RelationBaseAsync):
    __tablename__ = "business_entities_hierarchy"
    
    ref_entity_top: Mapped[int] = mapped_column(
        Integer, ForeignKey("business_entities.id", ondelete="CASCADE"), nullable=False
    , primary_key=True)
    ref_entity_bottom: Mapped[int] = mapped_column(
        Integer, ForeignKey("business_entities.id", ondelete="CASCADE"), nullable=False
    , primary_key=True)

    # Relationships
    entity_top: Mapped["BusinessEntity"] = relationship("BusinessEntity", foreign_keys=[ref_entity_top])
    entity_bottom: Mapped["BusinessEntity"] = relationship("BusinessEntity", foreign_keys=[ref_entity_bottom])
