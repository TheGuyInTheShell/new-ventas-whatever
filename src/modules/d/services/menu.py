import copy
from typing import Dict, Any, Set

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_injectable import injectable
from core.database import get_async_db
from core.lib.decorators.cache import func_cached
from core.lib.register.service import Service

from src.app.context.menu import MenuShields
from src.modules.permissions.models import Permission
from src.modules.role_permissions.models import RolePermission


class MenuService(Service):

    @func_cached(ttl=3600, prefix="menu:resolved:v3")
    @injectable
    async def get_resolved_menu(
        self, role_id: int, db: AsyncSession = Depends(get_async_db)
    ) -> Dict[str, Any]:
        """
        Calcula y devuelve el árbol del menú filtrado según los permisos
        asignados al rol del usuario. Hace uso de caché para evitar el recálculo.
        """
        try:
            # 1. Obtener conjunto de permisos UI a los que el rol tiene acceso
            query = (
                select(Permission.name)
                .join(RolePermission, Permission.id == RolePermission.permission_id)
                .where(
                    RolePermission.role_id == role_id,
                    Permission.type == "ui",
                )
            )
            result = await db.execute(query)
            allowed_names: Set[str] = set(result.scalars().all())

            print(f"[MenuService] role_id={role_id} allowed_names={allowed_names}")

            # 2. Obtener el esquema declarativo original
            raw_menu = MenuShields.to_consume()

            print(f"[MenuService] raw_menu keys={list(raw_menu.keys())}")

            # 3. Filtrar recursivamente
            filtered = self._filter_menu_tree(raw_menu, allowed_names)

            print(f"[MenuService] filtered keys={list(filtered.keys())}")

            return filtered
        finally:
            await db.close()

    def _filter_menu_tree(
        self,
        node_dict: Dict[str, Any],
        allowed_names: Set[str],
        depth: int = 0,
    ) -> Dict[str, Any]:
        """
        Filtra el árbol de menú recursivamente.

        depth=0 → nivel raíz del ShieldGroup. Los nodos aquí son entradas de
                  navegación de UI declaradas con Shield.can() directamente en
                  MenuShields. No tienen un permiso propio en la BD; su
                  visibilidad depende de sus hijos (si los tienen).
        depth>0 → hijos reales. Cada hoja requiere que su permiso exista en la
                  BD para el rol del usuario.
        """
        filtered_result = {}

        for key, node in node_dict.items():
            has_children = bool(node.get("children"))

            if has_children:
                # Contenedor (con o sin permiso propio en BD).
                # Se muestra si al menos un hijo pasa el filtro.
                node_copy = copy.deepcopy(node)
                filtered_children = self._filter_menu_tree(
                    node_copy["children"], allowed_names, depth=depth + 1
                )
                if filtered_children:
                    node_copy["children"] = filtered_children
                    filtered_result[key] = node_copy
            else:
                if depth == 0:
                    # Hoja en nivel raíz (ej. "profile"): entrada de nav UI pura.
                    # No requiere permiso en BD — todos los usuarios autenticados
                    # deben poder acceder a su perfil, etc.
                    filtered_result[key] = copy.deepcopy(node)
                else:
                    # Hoja en nivel hijo (ej. "settings.users"): requiere permiso
                    # explícito en la BD para este rol.
                    if node["name"] in allowed_names:
                        filtered_result[key] = copy.deepcopy(node)

        return filtered_result
