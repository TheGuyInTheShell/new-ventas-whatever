from sqlalchemy import Integer, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, List

from core.database import BasicBaseAsync

if TYPE_CHECKING:
    from src.modules.business_entities.models import BusinessEntity


class BusinessEntitiesGroup(BasicBaseAsync):
    __tablename__ = "business_entities_groups"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    business_entities: Mapped[List["BusinessEntity"]] = relationship("BusinessEntity", secondary="business_entities_groups_connections", back_populates="business_entities_groups")
