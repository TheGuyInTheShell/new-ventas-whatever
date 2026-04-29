from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from core.database import BasicBaseAsync

if TYPE_CHECKING:
    from src.modules.business_entities.models import BusinessEntity
    from src.modules.persons.meta.models import MetaPerson


class Person(BasicBaseAsync):
    __tablename__ = "persons"
    
    first_names: Mapped[str] = mapped_column(String(100), nullable=False)
    last_names: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=True)
    identifier: Mapped[str] = mapped_column(String(50), nullable=True)
    type_identifier: Mapped[str] = mapped_column(String(50), nullable=True)
    
    ref_business_entity: Mapped[int] = mapped_column(
        Integer, ForeignKey("business_entities.id", ondelete="CASCADE"), nullable=False
    )
    
    business_entity: Mapped["BusinessEntity"] = relationship("BusinessEntity")

    meta: Mapped[list["MetaPerson"]] = relationship("MetaPerson", back_populates="person")
