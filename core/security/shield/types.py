from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List

@dataclass(frozen=True, slots=True)
class PermissionMeta:
    """Metadata adicional de un permiso (key/value pair)."""
    key: str | None = None
    value: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {"key": self.key, "value": self.value}


@dataclass(frozen=True, slots=True)
class PermissionDefinition:
    """Definición inmutable de un permiso individual."""
    name: str
    action: str
    type: str
    description: str
    context: str
    meta: PermissionMeta = field(default_factory=PermissionMeta)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "action": self.action,
            "type": self.type,
            "description": self.description,
            "context": self.context,
            "meta": self.meta,
        }


@dataclass(slots=True)
class PermissionNode:
    """Nodo del árbol jerárquico de permisos por contexto."""
    permissions: List[PermissionDefinition] = field(default_factory=list)
    childs: Dict[str, PermissionNode] = field(default_factory=dict) # key: context name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "permissions": [p.to_dict() for p in self.permissions],
            "childs": [child_node.to_dict() for child_node in self.childs.values()]
        }
