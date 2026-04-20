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


class SysTemplate(Template):
    """Controlador de templates para la raíz de la aplicación pública."""

    @Get("/init", response_class=HTMLResponse)
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
            Script(src="/app-static/javascript/sys/init.js", type="module", defer=True)
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
