"""
Template controller para la raíz de app (/).

Este módulo define las rutas de la página principal de la aplicación pública.
"""

from fastapi import Request
from fastapi.responses import HTMLResponse

from core.lib.decorators import Get
from core.lib.register import Template
from core.services.ui.enqueue_js import enqueue_js, Site, Script
from core.services.ui.enqueue_css import enqueue_css, CssSite, Style

class SignTemplate(Template):
    """Controlador de templates para la raíz de la aplicación pública."""

    @Get("/in", response_class=HTMLResponse)
    @enqueue_css(css_tag=str(Style(href="/app-static/css/app.css", type="text/css", media="all")), position=CssSite.HEAD)
    @enqueue_js(js_tag=str(Script(src="/app-static/javascript/icons.js", type="module", defer=True)), position=Site.HEAD)
    @enqueue_js(js_tag=str(Script(src="/app-static/javascript/sign/in.js", type="module", defer=True)), position=Site.BODY_AFTER)
    async def sign_in(self, request: Request) -> HTMLResponse:
        """Renderiza la página de sign in de la aplicación.

        Args:
            request: Objeto Request de FastAPI.

        Returns:
            Respuesta HTML con la página principal renderizada.
        """

        return self.templates.TemplateResponse(
            request,
            name="pages/sign/in.html",
            context={
                "request": request,
            },
        )