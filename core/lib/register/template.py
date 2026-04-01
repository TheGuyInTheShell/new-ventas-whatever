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
    from fastapi.templating import Jinja2Templates


class Template:
    """Clase base para controladores de templates.

    Agnóstica del motor de renderizado. El proveedor de templates se inyecta
    en el constructor como ``Any``, desacoplando completamente la librería
    de cualquier implementación específica de renderizado.

    Attributes:
        templates: Instancia del proveedor de templates inyectado.
            Puede ser ``Jinja2Templates``, ``MakoTemplates``, o cualquier
            otro motor compatible.
    """

    templates: Union["Jinja2Templates", Any]

    def __init__(self, template_provider: Union["Jinja2Templates", Any]) -> None:
        """Inicializa el controlador con el proveedor de templates.

        Args:
            template_provider: Instancia del motor de renderizado de templates.
                Se almacena como ``self.templates`` para uso en los handlers.
        """
        self.templates = template_provider
