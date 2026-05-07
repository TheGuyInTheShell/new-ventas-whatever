from sqlalchemy import String, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import RelationBaseAsync
from src.modules.users.models import User

class MetaUsers(RelationBaseAsync):
    __tablename__ = "meta_users"
    key: Mapped[str] = mapped_column(String(100), primary_key=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    
    ref_user: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, primary_key=True)
    user: Mapped[User] = relationship()

    __table_args__ = (
        Index("idx_meta_users_key_ref_user", "key", "ref_user", unique=True),
    )
