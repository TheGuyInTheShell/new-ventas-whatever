from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List, Tuple, Type


# ---------------------------------------------------------------------------
# PermissionMeta — ahora soporta múltiples pares key/value
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class PermissionMeta:
    """Colección inmutable de pares key/value para metadata extendida de un permiso."""

    pairs: Tuple[Tuple[Optional[str], Optional[str]], ...] = field(default_factory=tuple)

    @classmethod
    def from_list(cls, meta: List[Tuple[Optional[str], Optional[str]]]) -> "PermissionMeta":
        """Construye un PermissionMeta desde una lista de tuplas [(key, value), ...]."""
        return cls(pairs=tuple(meta))

    def to_dict(self) -> List[Dict[str, Any]]:
        """Serializa como lista de objetos {key, value}."""
        return [{"key": k, "value": v} for k, v in self.pairs]


# ---------------------------------------------------------------------------
# PermissionDefinition — descriptor inmutable de un permiso individual
# ---------------------------------------------------------------------------

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
            "meta": self.meta.to_dict(),
        }


# ---------------------------------------------------------------------------
# PermissionNode — nodo interno del árbol del PermissionRegistry
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class PermissionNode:
    """Nodo del árbol jerárquico de permisos por contexto (uso interno del registry)."""

    permissions: List[PermissionDefinition] = field(default_factory=list)
    childs: Dict[str, "PermissionNode"] = field(default_factory=dict)  # key: context name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "permissions": [p.to_dict() for p in self.permissions],
            "childs": [child_node.to_dict() for child_node in self.childs.values()],
        }


# ---------------------------------------------------------------------------
# CanNode — descriptor fluido retornado por Shield.can()
# ---------------------------------------------------------------------------

class CanNode:
    """
    Descriptor fluido de un permiso declarado manualmente mediante ``Shield.can()``.

    Soporta encadenamiento de hijos mediante ``.children(ChildrenClass)``.

    Ejemplo::

        Shield.can(
            "chinese_restaurant", "read", "ui",
            description="Acceso al módulo de restaurante chino",
            meta=[("icon", "mdi-food-fork-drink")],
        ).children(ChineseRestaurantChildren)
    """

    def __init__(
        self,
        name: str,
        action: str,
        type_str: str,
        description: str,                                          # requerido, sin default
        meta: Optional[List[Tuple[Optional[str], Optional[str]]]] = None,
    ) -> None:
        self.name: str = name
        self.action: str = action
        self.type: str = type_str
        self.description: str = description
        self.meta: List[Tuple[Optional[str], Optional[str]]] = meta or []
        self._children_cls: Optional[Type] = None

    # ------------------------------------------------------------------
    # Fluent API
    # ------------------------------------------------------------------

    def children(self, children_cls: Type) -> "CanNode":
        """Encadena una clase de permisos hijos a este nodo."""
        self._children_cls = children_cls
        return self

    # ------------------------------------------------------------------
    # Conversión al sistema de registry
    # ------------------------------------------------------------------

    def to_permission_definition(self, context: str) -> PermissionDefinition:
        """Convierte este descriptor a un ``PermissionDefinition`` para el registry global."""
        return PermissionDefinition(
            name=self.name,
            action=self.action,
            type=self.type,
            description=self.description,
            context=context,
            meta=PermissionMeta.from_list(self.meta),
        )

    # ------------------------------------------------------------------
    # Representación de depuración
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        children = f" → {self._children_cls.__name__}" if self._children_cls else ""
        return (
            f"<CanNode name={self.name!r} action={self.action!r}"
            f" type={self.type!r}{children}>"
        )
