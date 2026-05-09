import copy
from typing import Dict, Any, Set

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_injectable import injectable
from core.database import get_async_db
from core.lib.decorators.cache import func_cached
from core.lib.decorators import Services
from core.lib.register.service import Service

from src.app.context.menu import MenuShields
from src.modules.permissions.models import Permission
from src.modules.role_permissions.models import RolePermission

from fastcore.xml import Div, Ul, Li, A, Details, Summary, I, Span, to_xml

from src.modules.users.services import UsersService


@Services(UsersService)
class MenuService(Service):

    UsersService: "UsersService"

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

            # 2. Obtener el esquema declarativo original
            raw_menu = MenuShields.to_consume()

            # 3. Filtrar recursivamente
            filtered = self._filter_menu_tree(raw_menu, allowed_names)

            return filtered
        except Exception as e:
            print(f"Error in get_resolved_menu: {e}")
            raise e

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

    async def get_menu_component(self, request: Request) -> str:
        user, error = await self.UsersService.get_current_user_app(request)
        if error or not user:
            return ""

        role_id = int(user.role)

        # 1. Obtener el diccionario del menú resuelto (filtrado y cacheado por rol)
        menu_tree = await self.get_resolved_menu(role_id=role_id)

        # 2. Construir nodos FastCore
        items = []

        # Opcional: Quick Search fijo al principio de la barra
        items.append(
            Div(
                A(
                    I(data_lucide="search", cls="size-4 shrink-0"),
                    Span("Search...", cls="ml-2 is-drawer-close:hidden"),
                    href="#",
                    cls="flex items-center w-full px-2 py-2 text-xs text-base-content/60 border border-base-300 rounded-lg hover:bg-base-300 transition-colors is-drawer-close:justify-center is-drawer-close:tooltip is-drawer-close:tooltip-right",
                    data_tip="Quick Search (⌘K)",
                ),
                cls="px-1 mb-4",
            )
        )

        for key, node in menu_tree.items():
            items.append(self._build_menu_node(key, node))

        # 3. Retornar contenedor principal HTML
        content = to_xml(Ul(*items, cls="menu p-0 w-full gap-1"))
        return content

    def _build_menu_node(self, key: str, node: dict):
        # Extraer icono, ruta y nombre del meta si existe
        meta_list = node.get("meta", [])
        icon = "circle"  # default
        route = "#"
        display_name = node.get("description") or key.replace("_", " ").title()

        for item in meta_list:
            if isinstance(item, dict):
                k = item.get("key")
                v = item.get("value")
                if k == "icon":
                    icon = v
                elif k == "route":
                    route = v
                elif k == "name":
                    display_name = v

        # Limpiamos prefijo mdi- por compatibilidad si es necesario,
        # pero se usará el valor directo que viene de base de datos
        lucide_icon = icon.replace("mdi-", "") if icon.startswith("mdi-") else icon

        icon_elem = I(
            data_lucide=lucide_icon,
            cls="size-5 shrink-0 transition-premium group-hover:scale-110 hover:text-white",
        )

        # Si el nodo padre tiene hijos, renderizar el desplegable <details>
        if "children" in node and node["children"]:
            summary = Summary(
                icon_elem,
                A(
                    display_name,
                    href=route,
                    cls="flex-1 text-left is-drawer-close:hidden font-medium hover:text-white transition-colors",
                ),
                cls="sidebar-item hover:scale-[1.02] hover:text-white is-drawer-close:justify-center is-drawer-close:tooltip is-drawer-close:tooltip-right",
                data_tip=display_name,
            )

            child_items = []
            for child_key, child_node in node["children"].items():
                child_meta_list = child_node.get("meta", [])
                child_route = "#"
                child_display = (
                    child_node.get("description") or child_key.replace("_", " ").title()
                )

                for item in child_meta_list:
                    if isinstance(item, dict):
                        chk = item.get("key")
                        chv = item.get("value")
                        if chk == "route":
                            child_route = chv
                        elif chk == "name":
                            child_display = chv

                child_items.append(
                    Li(
                        A(
                            child_display,
                            href=child_route,
                            cls="text-xs py-1.5 transition-premium hover:text-white hover:translate-x-1 inline-block text-base-content/70",
                        )
                    )
                )

            ul = Ul(
                *child_items,
                cls="is-drawer-close:hidden mt-1 ml-4 border-l border-base-300 pl-4 space-y-1",
            )

            return Li(
                Details(
                    summary,
                    ul,
                    x_data="{ open: false }",
                    **{"@toggle": "open = $event.target.open"},
                    cls="group",
                )
            )

        # Caso base: un menú principal directo (ej. profile) sin desplegable
        else:
            link = A(
                icon_elem,
                Span(display_name, cls="is-drawer-close:hidden font-medium"),
                href=route,
                cls="sidebar-item hover:scale-[1.02] is-drawer-close:justify-center is-drawer-close:tooltip is-drawer-close:tooltip-right hover:text-white",
                data_tip=display_name,
            )
            return Li(link, cls="group")
