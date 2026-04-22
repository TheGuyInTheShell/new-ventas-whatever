"""
Template controller para /app/dashboard.

Este módulo define las rutas del dashboard de la aplicación pública.
"""

from fastapi import Request
from fastapi.responses import HTMLResponse

from core.lib.decorators import Get, Services
from core.lib.register import Template
from core.services.ui.enqueue_js import enqueue_js, Site, Script
from core.services.ui.enqueue_css import enqueue_css, CssSite, Style
from core.security.shield import Shield

from src.modules.auth.services import AuthService
from src.modules.users.services import UsersService
from src.modules.d.services.menu import MenuService

from fasthtml.common import Div, Ul, Li, A, Details, Summary, I, Span, to_xml


@Services(AuthService, UsersService, MenuService)
@Shield.register(context="Dashboard")
class Dashboard(Template):
    """Controlador de templates para la sección dashboard de la aplicación."""

    AuthService: "AuthService"
    UsersService: "UsersService"
    MenuService: "MenuService"

    @Get("/", response_class=HTMLResponse)
    @Shield.need(
        name="dashboard",
        action="read",
        type="template",
        description="Permite acceder al dashboard.",
    )
    @enqueue_css(
        css_tag=str(
            Style(href="/app-static/css/app.css", type="text/css", media="all")
        ),
        position=CssSite.HEAD,
    )
    @enqueue_js(
        js_tag=str(
            Script(src="/app-static/javascript/icons.js", type="module", defer=True)
        ),
        position=Site.HEAD,
    )
    @enqueue_js(
        js_tag=str(
            Script(src="/app-static/javascript/index.js", type="module", defer=True)
        ),
        position=Site.BODY_AFTER,
    )
    async def dashboard_index(self, request: Request) -> HTMLResponse:
        """Renderiza la página principal del dashboard de la aplicación.

        Args:
            request: Objeto Request de FastAPI.

        Returns:
            Respuesta HTML con el dashboard renderizado.
        """
        return self.templates.TemplateResponse(
            request,
            name="pages/dashboard/index.html",
            context={
                "request": request,
                "menu": await self.get_menu_component(request),
            },
        )

    async def get_menu_component(self, request: Request) -> str:
        user = await self.UsersService.get_current_user_app(request)

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
