"""
Template controller para la raíz de admin (/admin).

Este módulo define las rutas de la página principal del panel de administración.
"""

from fastapi import Request
from fastapi.responses import HTMLResponse

from core.lib.decorators import Get
from core.lib.register import Template


class Index(Template):
    """Controlador de templates para la raíz del panel de administración."""

    @Get("/", response_class=HTMLResponse)
    async def main_dashboard(self, request: Request) -> HTMLResponse:
        """Renderiza la página principal del panel de administración.

        Args:
            request: Objeto Request de FastAPI.

        Returns:
            Respuesta HTML con la página principal renderizada.
        """
        return self.templates.TemplateResponse(
            request,
            name="pages/dashboard.html",
            context={
                "request": request,
            },
        )
