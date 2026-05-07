from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import RelationBaseAsync

class RolePermission(RelationBaseAsync):
    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    , primary_key=True)
    permission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False
    , primary_key=True)

    # Relationships (Optional, but useful)
    role = relationship("src.modules.roles.models.Role", backref="role_permission_entries")
    permission = relationship("src.modules.permissions.models.Permission", backref="role_permission_entries")
