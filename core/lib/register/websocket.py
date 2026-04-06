"""
Clase base Template para controladores de vistas con templates.

Proporciona una clase base agnóstica del motor de renderizado (Jinja2, Mako,
Django Templates, etc.). El proveedor de templates se inyecta en el constructor
como un objeto genérico (``Any``), permitiendo que cualquier motor de renderizado
sea utilizado sin acoplar la librería a una implementación específica.

Uso típico::

    from core.lib.register import Template
    from core.lib.decorators import Get

    class Dashboard(Template):

        @Get("/", response_class=HTMLResponse)
        async def index(self, request: Request) -> HTMLResponse:
            return self.templates.TemplateResponse(
                request,
                name="pages/dashboard.html",
                context={"request": request},
            )
"""
from typing import TYPE_CHECKING, Union, Any

if TYPE_CHECKING:
    from socketio import AsyncServer


class WebSocket:
    """Clase base para controladores de websockets.
    """


    def __init__(self, sio: Union["AsyncServer", Any], module_name: str) -> None:
        """Inicializa el controlador con el proveedor de templates.

        Args:
            template_provider: Instancia del motor de renderizado de templates.
                Se almacena como ``self.templates`` para uso en los handlers.
        """
        self.sio = sio
        self.module_name = module_name
        self.namespace = f"/{module_name}"
