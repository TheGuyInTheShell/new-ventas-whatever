"""
Template controller para /admin/dashboard.

Este módulo define las rutas de la sección dashboard del panel de administración.
"""

from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse

from core.lib.decorators import Get
from core.lib.register import Template


class Dashboard(Template):
    """Controlador de templates para la sección dashboard de admin."""

    @Get("/", response_class=HTMLResponse)
    async def dashboard_index(self, request: Request) -> HTMLResponse:
        """Renderiza la página principal del dashboard de administración.

        Args:
            request: Objeto Request de FastAPI.

        Returns:
            Respuesta HTML con el dashboard renderizado.
        """
        return self.templates.TemplateResponse(
            request,
            name="pages/index.html",
            context={
                "request": request,
            },
        )
