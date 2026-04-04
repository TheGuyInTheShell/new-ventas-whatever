from sqlalchemy import String, Text, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from core.database import BaseAsync


class Options(BaseAsync):
    __tablename__ = "options"
    context: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("idx_options_context", "context"),
        Index("idx_options_name", "name"),
        UniqueConstraint("context", "name", name="uq_options_context_name"),
    )