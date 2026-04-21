from core.lib.decorators import Get, Services
from core.lib.register import Partial

from src.modules.auth.services import AuthService
from src.modules.users.services import UsersService
from src.modules.d.services.menu import MenuService
from fastapi.responses import HTMLResponse
from fasthtml.common import Div, Ul, Li, A, Details, Summary, I, Span, to_xml
from core.security.shield.shield import Shield
from fastapi import Request


@Services(AuthService, UsersService, MenuService)
@Shield.register(context="Menu")
class MenuPartial(Partial):

    AuthService: "AuthService"
    UsersService: "UsersService"
    MenuService: "MenuService"

    @Get("/", response_class=HTMLResponse)
    @Shield.need(
        name="menu",
        action="read",
        type="ui",
        description="Permite renderizar dinámicamente la barra de navegación del menú",
    )
    async def get_menu_partial(self, request: Request) -> HTMLResponse:

        user = await self.UsersService.get_current_user_app(request)
        if not user:
            return HTMLResponse(content="", status_code=200)

        role_id = int(user.role)

        # 1. Obtener el diccionario del menú resuelto (filtrado y cacheado por rol)
        menu_tree = await self.MenuService.get_resolved_menu(role_id=role_id)

        # 2. Construir nodos FastHTML
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

        return HTMLResponse(content=content, status_code=200)

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
            cls="size-5 shrink-0 transition-premium group-hover:scale-110",
        )

        # Si el nodo padre tiene hijos, renderizar el desplegable <details>
        if "children" in node and node["children"]:
            summary = Summary(
                icon_elem,
                A(
                    display_name,
                    href=route,
                    cls="flex-1 text-left is-drawer-close:hidden font-medium hover:text-primary transition-colors",
                ),
                cls="sidebar-item hover:scale-[1.02] is-drawer-close:justify-center is-drawer-close:tooltip is-drawer-close:tooltip-right",
                data_tip=display_name,
            )

            child_items = []
            for child_key, child_node in node["children"].items():
                child_meta_list = child_node.get("meta", [])
                child_route = "#"
                child_display = child_node.get("description") or child_key.replace("_", " ").title()

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
                            cls="text-xs py-1.5 transition-premium hover:text-primary hover:translate-x-1 inline-block text-base-content/70",
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
                cls="sidebar-item hover:scale-[1.02] is-drawer-close:justify-center is-drawer-close:tooltip is-drawer-close:tooltip-right",
                data_tip=display_name,
            )
            return Li(link, cls="group")
