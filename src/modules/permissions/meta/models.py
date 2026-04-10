from sqlalchemy import String, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import BasicBaseAsync
from typing import TYPE_CHECKING

from src.modules.permissions.models import Permission


class MetaPermissions(BasicBaseAsync):
    __tablename__ = "meta_permissions"
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    
    ref_permission: Mapped[int]  = mapped_column(ForeignKey("permissions.id"), nullable=False)
    permission: Mapped[Permission] = relationship()

    __table_args__ = (
        Index("idx_meta_permissions_key_ref_permission", "key", "ref_permission", unique=True),
    )