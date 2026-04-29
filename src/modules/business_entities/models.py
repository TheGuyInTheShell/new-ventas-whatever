from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from core.database import BasicBaseAsync

if TYPE_CHECKING:
    from src.modules.business_entities.meta.models import MetaBusinessEntity
    from src.modules.business_entities_groups.models import BusinessEntitiesGroup


class BusinessEntity(BasicBaseAsync):
    __tablename__ = "business_entities"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    meta: Mapped[list["MetaBusinessEntity"]] = relationship(
        "MetaBusinessEntity", back_populates="business_entity"
    )
    business_entities_groups: Mapped[list["BusinessEntitiesGroup"]] = relationship(
        "BusinessEntitiesGroup",
        secondary="business_entities_groups_connections",
        back_populates="business_entities",
    )
