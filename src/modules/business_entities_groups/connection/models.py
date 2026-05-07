from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from core.database import RelationBaseAsync

if TYPE_CHECKING:
    from src.modules.business_entities_groups.models import BusinessEntitiesGroup
    from src.modules.business_entities.models import BusinessEntity


class BusinessEntitiesGroupConnection(RelationBaseAsync):
    __tablename__ = "business_entities_groups_connections"

    ref_business_entities_group: Mapped[int] = mapped_column(
        Integer, ForeignKey("business_entities_groups.id"), nullable=False, primary_key=True
    )
    ref_business_entities: Mapped[int] = mapped_column(
        Integer, ForeignKey("business_entities.id", ondelete="CASCADE"), nullable=False, primary_key=True
    )

    # Relationships
    business_entities_group: Mapped["BusinessEntitiesGroup"] = relationship(
        "BusinessEntitiesGroup",
        foreign_keys=[ref_business_entities_group],
        overlaps="business_entities,business_entities_groups",
    )
    business_entity: Mapped["BusinessEntity"] = relationship(
        "BusinessEntity",
        foreign_keys=[ref_business_entities],
        overlaps="business_entities,business_entities_groups",
    )

    __table_args__ = (
        UniqueConstraint(
            "ref_business_entities_group",
            "ref_business_entities",
            name="uq_business_entities_groups_connections",
        ),
    )
