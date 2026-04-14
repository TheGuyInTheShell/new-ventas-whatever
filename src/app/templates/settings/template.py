from fastapi import Request
from fastapi.responses import HTMLResponse

from core.lib.decorators import Get
from core.lib.register import Template
from core.services.ui.enqueue_js import enqueue_js, Site, Script
from core.services.ui.enqueue_css import enqueue_css, CssSite, Style
from core.security.csrf.csrf import CSRF

class SettingsTemplate(Template):
    """Controlador de templates para Settings."""

    @Get("/", response_class=HTMLResponse)
    @enqueue_css(css_tag=str(Style(href="/app-static/css/app.css", type="text/css", media="all")), position=CssSite.HEAD)
    @enqueue_js(js_tag=str(Script(src="/app-static/javascript/icons.js", type="module", defer=True)), position=Site.HEAD)
    @CSRF()
    async def settings_index(self, request: Request) -> HTMLResponse:
        return self.templates.TemplateResponse(
            request,
            name="pages/settings/index.html",
            context={
                "request": request,
            },
        )

    @Get("/profile", response_class=HTMLResponse)
    @enqueue_css(css_tag=str(Style(href="/app-static/css/app.css", type="text/css", media="all")), position=CssSite.HEAD)
    @enqueue_js(js_tag=str(Script(src="/app-static/javascript/icons.js", type="module", defer=True)), position=Site.HEAD)
    @CSRF()
    async def profile(self, request: Request) -> HTMLResponse:
        return self.templates.TemplateResponse(
            request,
            name="pages/settings/profile.html",
            context={"request": request},
        )

    @Get("/fiat", response_class=HTMLResponse)
    @enqueue_css(css_tag=str(Style(href="/app-static/css/app.css", type="text/css", media="all")), position=CssSite.HEAD)
    @enqueue_js(js_tag=str(Script(src="/app-static/javascript/icons.js", type="module", defer=True)), position=Site.HEAD)
    @enqueue_js(js_tag=str(Script(src="/app-static/javascript/store/fiatStore.js", type="module", defer=True)), position=Site.HEAD)
    @enqueue_js(js_tag=str(Script(src="/app-static/javascript/settings/fiat.js", type="module", defer=True)), position=Site.HEAD)
    @CSRF()
    async def fiat(self, request: Request) -> HTMLResponse:
        return self.templates.TemplateResponse(
            request,
            name="pages/settings/fiat.html",
            context={"request": request},
        )

    @Get("/members", response_class=HTMLResponse)
    @enqueue_css(css_tag=str(Style(href="/app-static/css/app.css", type="text/css", media="all")), position=CssSite.HEAD)
    @enqueue_js(js_tag=str(Script(src="/app-static/javascript/icons.js", type="module", defer=True)), position=Site.HEAD)
    @CSRF()
    async def members(self, request: Request) -> HTMLResponse:
        return self.templates.TemplateResponse(
            request,
            name="pages/settings/members.html",
            context={"request": request},
        )

    @Get("/notifications", response_class=HTMLResponse)
    @enqueue_css(css_tag=str(Style(href="/app-static/css/app.css", type="text/css", media="all")), position=CssSite.HEAD)
    @enqueue_js(js_tag=str(Script(src="/app-static/javascript/icons.js", type="module", defer=True)), position=Site.HEAD)
    @CSRF()
    async def notifications(self, request: Request) -> HTMLResponse:
        return self.templates.TemplateResponse(
            request,
            name="pages/settings/notifications.html",
            context={"request": request},
        )

    @Get("/security", response_class=HTMLResponse)
    @enqueue_css(css_tag=str(Style(href="/app-static/css/app.css", type="text/css", media="all")), position=CssSite.HEAD)
    @enqueue_js(js_tag=str(Script(src="/app-static/javascript/icons.js", type="module", defer=True)), position=Site.HEAD)
    @CSRF()
    async def security(self, request: Request) -> HTMLResponse:
        return self.templates.TemplateResponse(
            request,
            name="pages/settings/security.html",
            context={"request": request},
        )