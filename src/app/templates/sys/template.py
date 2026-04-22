"""
Template controller para la raíz de app (/).

Este módulo define las rutas de la página para el primer registro del sistema.
"""

from fastapi import Request
from fastapi.responses import HTMLResponse

from core.lib.decorators import Get
from core.lib.register import Template
from core.services.ui.enqueue_js import enqueue_js, Site, Script
from core.services.ui.enqueue_css import enqueue_css, CssSite, Style
from core.security.shield import Shield
from src.modules.auth.shields import SysInitShield


@Shield.register(context="Sys")
class SysTemplate(Template):
    """Controlador de templates para la raíz de la aplicación pública."""

    @Get("/init", response_class=HTMLResponse)
    @Shield.need(
        name="sys",
        action="init",
        type="template",
        description="Permite acceder al primer registro del sistema.",
        resolver=SysInitShield(),
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
            Script(
                src="/app-static/javascript/pages/sys/init.js",
                type="module",
                defer=True,
            )
        ),
        position=Site.BODY_AFTER,
    )
    async def init_sys(self, request: Request) -> HTMLResponse:
        """Renderiza la página para el primer registro del sistema.

        Args:
            request: Objeto Request de FastAPI.

        Returns:
            Respuesta HTML con la página para el primer registro del sistema.
        """

        return self.templates.TemplateResponse(
            request,
            name="pages/sys/init.html",
            context={
                "request": request,
            },
        )
