from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import BasicBaseAsync


class Permission(BasicBaseAsync):
    __tablename__ = "permissions"
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    context: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
