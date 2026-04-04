from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from core.database import BaseAsync

if TYPE_CHECKING:
    from app.modules.business_entities.meta.models import MetaBusinessEntity
    from app.modules.business_entities_groups.models import BusinessEntitiesGroup


class BusinessEntity(BaseAsync):
    __tablename__ = "business_entities"
    
    context: Mapped[str] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=True)
    metadata_info: Mapped[dict] = mapped_column("metadata", JSON, nullable=True)
    meta: Mapped[list["MetaBusinessEntity"]] = relationship("MetaBusinessEntity", back_populates="business_entity")
    business_entities_groups: Mapped[list["BusinessEntitiesGroup"]] = relationship(
        "BusinessEntitiesGroup", 
        secondary="business_entities_groups_connections", 
        back_populates="business_entities"
    )

