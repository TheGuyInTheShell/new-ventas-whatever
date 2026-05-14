from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Type

from .errors import ShieldRegistryError
from .registry import permission_registry
from .types import CanNode, PermissionDefinition


class ShieldGroup:
    """
    Clase base heredable para definir árboles de permisos de forma declarativa.

    Reemplaza al decorador ``@Shield.have()``.  El contexto raíz se declara
    mediante el atributo de clase ``__context__``.  Al definir la clase hija,
    ``__init_subclass__`` registra automáticamente todos los ``CanNode``
    encontrados en el cuerpo de la clase (y sus hijos) en el
    ``PermissionRegistry`` global.

    Métodos heredados
    -----------------
    to_dict()
        Retorna el árbol con el mismo schema del ``PermissionRegistry``::

            {
              "permissions": [
                {
                  "permissions": [...],
                  "childs": [...]
                }
              ]
            }

    to_consume()
        Retorna un schema simplificado pensado para consumo en frontend o
        lógica de aplicación::

            {
              "chinese_restaurant": {
                "name": "chinese_restaurant",
                "action": "read",
                "type": "ui",
                "context": "Menu",
                "description": "...",
                "meta": [{"key": "icon", "value": "mdi-food-fork-drink"}],
                "children": { ... }
              }
            }

    Ejemplo de uso::

        class ChineseRestaurantChildren:
            menu = Shield.can(
                "chinese_restaurant.menu", "read", "ui",
                description="Ver menú",
                meta=[("icon", "mdi-food-fork-drink")],
            )

        class MenuShields(ShieldGroup):
            __context__ = "Menu"

            chinese_restaurant = Shield.can(
                "chinese_restaurant", "read", "ui",
                description="Módulo restaurante chino",
                meta=[("icon", "mdi-food-fork-drink")],
            ).children(ChineseRestaurantChildren)

            profile = Shield.can(
                "profile", "read", "ui",
                description="Perfil de usuario",
                meta=[("icon", "mdi-account")],
            )

        # Obtener árbol en formato registry
        MenuShields.to_dict()

        # Obtener árbol simplificado para consumo
        MenuShields.to_consume()
    """

    # Atributo que identifica el contexto raíz de este grupo de permisos.
    # Debe ser sobreescrito en cada subclase.
    __context__: str = ""

    # Marcador detectado por el Scanner para identificar grupos declarativos.
    __shield_group_marker__: bool = True

    # ------------------------------------------------------------------
    # Hook de clase
    # ------------------------------------------------------------------

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Solo registramos clases concretas (no la propia ShieldGroup base)
        if cls is not ShieldGroup:
            cls._register_all()

    # ------------------------------------------------------------------
    # Recolección de descriptores
    # ------------------------------------------------------------------

    @classmethod
    def _collect_nodes(cls) -> Dict[str, CanNode]:
        """
        Recolecta todos los atributos de clase que sean instancias de ``CanNode``.
        El orden es el de definición (Python 3.7+ garantiza dict ordering en __dict__).
        """
        return {
            attr: value
            for attr, value in vars(cls).items()
            if isinstance(value, CanNode)
        }

    # ------------------------------------------------------------------
    # Registro en el PermissionRegistry global
    # ------------------------------------------------------------------

    @classmethod
    def _register_all(cls) -> None:
        """
        Registra todos los ``CanNode`` de la clase (y sus sub-clases de hijos)
        en el ``PermissionRegistry`` global.

        Estructura registrada:

        - Nodo raíz ``__context__`` → contiene todos los permisos de nivel 1.
        - Por cada CanNode con ``.children(ChildrenClass)``:
            - Se crea un nodo hijo cuyo contexto = ``can_node.name``
            - Sus permisos se registran con ``parent_context = __context__``
        """
        context: str = cls.__context__ or cls.__name__
        top_nodes = cls._collect_nodes()

        for _attr, can_node in top_nodes.items():
            # 1. Permiso de nivel 1 en el contexto raíz
            definition = can_node.to_permission_definition(context)
            _safe_add(definition, parent_context=None)

            # 2. Permisos de los hijos (si existen)
            if can_node._children_cls is not None:
                child_context: str = can_node.name  # ej. "chinese_restaurant"
                for child_attr, child_can in vars(can_node._children_cls).items():
                    if isinstance(child_can, CanNode):
                        child_def = child_can.to_permission_definition(child_context)
                        _safe_add(child_def, parent_context=context)

    # ------------------------------------------------------------------
    # API pública — serialización
    # ------------------------------------------------------------------

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """
        Retorna el árbol de permisos de este grupo con el mismo schema
        que ``PermissionRegistry.to_dict()``::

            {
              "permissions": [
                { "permissions": [...], "childs": [...] }
              ]
            }
        """
        context: str = cls.__context__ or cls.__name__
        node = permission_registry.get_node(context)
        if node is not None:
            return {"permissions": [node.to_dict()]}
        return {"permissions": []}

    @classmethod
    def to_consume(cls) -> Dict[str, Any]:
        """
        Retorna un schema simplificado por nombre de propiedad, pensado para
        consumo en frontend o lógica de aplicación::

            {
              "chinese_restaurant": {
                "name": "chinese_restaurant",
                "action": "read",
                "type": "ui",
                "context": "Menu",
                "description": "...",
                "meta": [{"key": "icon", "value": "mdi-food-fork-drink"}],
                "children": {
                  "menu": { "name": "chinese_restaurant.menu", ... }
                }
              },
              "profile": { ... }
            }
        """
        context: str = cls.__context__ or cls.__name__
        result: Dict[str, Any] = {}

        for attr_name, can_node in cls._collect_nodes().items():
            entry: Dict[str, Any] = {
                "name": can_node.name,
                "action": can_node.action,
                "type": can_node.type,
                "context": context,
                "description": can_node.description,
                "meta": [{"key": k, "value": v} for k, v in can_node.meta],
            }

            if can_node._children_cls is not None:
                child_context = can_node.name
                entry["children"] = {
                    child_attr: {
                        "name": child_can.name,
                        "action": child_can.action,
                        "type": child_can.type,
                        "context": child_context,
                        "description": child_can.description,
                        "meta": [{"key": k, "value": v} for k, v in child_can.meta],
                    }
                    for child_attr, child_can in vars(can_node._children_cls).items()
                    if isinstance(child_can, CanNode)
                }

            result[attr_name] = entry

        return result

    # ------------------------------------------------------------------
    # Representación de depuración
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        context = self.__context__ or type(self).__name__
        nodes = list(self._collect_nodes().keys())
        return f"<ShieldGroup context={context!r} nodes={nodes}>"


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------


def _safe_add(definition: PermissionDefinition, parent_context: Optional[str]) -> None:
    """Agrega una definición al registry ignorando duplicados (re-import protection)."""
    try:
        permission_registry.add(definition, parent_context=parent_context)
    except ShieldRegistryError:
        pass
