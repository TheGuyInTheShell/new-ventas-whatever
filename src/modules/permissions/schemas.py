from datetime import datetime
from typing import List

from pydantic import BaseModel


class QueryPermission(BaseModel):
    name: str
    type: str
    context: str


class CreatePermission(BaseModel):
    """Schema para crear un permiso individual"""
    name: str
    action: str
    description: str
    type: str


class BulkPermission(BaseModel):
    """Schema para crear un permiso dentro de un bulk"""
    name: str
    action: str
    description: str
    type: str
    meta: dict | list | None = None
    role_id: int | str


class BulkPermissions(BaseModel):
    """Schema para crear múltiples permisos con sus roles asociados"""
    permissions: List[BulkPermission]


class PermissionResult(BaseModel):
    uid: str
    id: int
    type: str
    name: str
    action: str
    description: str
    meta: dict | list | None = None


class BulkPermissionResult(BaseModel):
    """Schema para el resultado de la creación de un permiso en bulk"""
    permission: PermissionResult
    role_id: int | str
    success: bool
    error: str | None = None


class BulkPermissionsResponse(BaseModel):
    """Schema para la respuesta de creación en bulk"""
    created: List[BulkPermissionResult]
    total: int
    success_count: int
    error_count: int


class PermissionPaginated(BaseModel):
    data: list[PermissionResult] | List = []
    total: int = 0
    page: int | None = 0
    page_size: int | None = 0
    total_pages: int | None = 0
    has_next: bool | None = False
    has_prev: bool | None = False
    next_page: int | None = 0
    prev_page: int | None = 0


class UserMe(BaseModel):
    """Response schema for /users/me."""
    id: int | str
    uid: str
    username: str
    email: str
    full_name: str
    role: int | str
    role_name: str
    otp_enabled: bool = False
    permissions: List[PermissionResult] = []
