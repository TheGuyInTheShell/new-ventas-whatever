from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import BaseAsync

if TYPE_CHECKING:
    from app.modules.persons.models import Person

class MetaPerson(BaseAsync):
    __tablename__ = "meta_persons"
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    ref_person: Mapped[int] = mapped_column(Integer, ForeignKey("persons.id"), nullable=False)
    person: Mapped["Person"] = relationship("Person", foreign_keys=[ref_person])

    __table_args__ = (
        Index("idx_values_meta_ref_person", "key", "ref_person", unique=True),
    )
