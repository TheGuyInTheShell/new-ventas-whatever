from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import BaseAsync

if TYPE_CHECKING:
    from app.modules.business_entities.models import BusinessEntity

class MetaBusinessEntity(BaseAsync):
    __tablename__ = "meta_business_entities"
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    ref_business_entity: Mapped[int] = mapped_column(Integer, ForeignKey("business_entities.id"), nullable=False)
    business_entity: Mapped["BusinessEntity"] = relationship("BusinessEntity", foreign_keys=[ref_business_entity])

    __table_args__ = (
        Index("idx_values_meta_ref_business_entity", "key", "ref_business_entity", unique=True),
    )
    