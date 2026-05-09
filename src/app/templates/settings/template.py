from fastapi import Request
from fastapi.responses import HTMLResponse

from core.lib.decorators import Get, Services
from core.lib.register import Template
from core.services.ui.enqueue_js import enqueue_js, Site, Script
from core.services.ui.enqueue_css import enqueue_css, CssSite, Style
from core.security.csrf.csrf import CSRF
from core.security.shield import Shield

from src.domain.services.menu import MenuService


@Services(MenuService)
@Shield.register(context="WEB")
class SettingsTemplate(Template):
    """Controlador de templates para Settings."""

    MenuService: "MenuService"

    @Get("/", response_class=HTMLResponse)
    @Shield.need(
        name="settings",
        action="read",
        type="template",
        description="view settings",
    )
    @enqueue_css(
        css_tag=str(
            Style(href="/app-static/css/app.css", type="text/css", media="all")
        ),
        position=CssSite.HEAD,
    )
    @enqueue_js(
        js_tag=str(Script(src="/app-static/ts/icons.js", type="module", defer=True)),
        position=Site.HEAD,
    )
    @CSRF()
    async def settings_index(self, request: Request) -> HTMLResponse:
        return self.templates.TemplateResponse(
            request,
            name="pages/settings/index.html",
            context={
                "request": request,
                "menu": await self.MenuService.get_menu_component(request),
            },
        )

    @Get("/profile", response_class=HTMLResponse)
    @Shield.need(
        name="profile",
        action="read",
        type="template",
        description="view profile",
    )
    @enqueue_css(
        css_tag=str(
            Style(href="/app-static/css/app.css", type="text/css", media="all")
        ),
        position=CssSite.HEAD,
    )
    @enqueue_js(
        js_tag=str(Script(src="/app-static/ts/icons.js", type="module", defer=True)),
        position=Site.HEAD,
    )
    @CSRF()
    async def profile(self, request: Request) -> HTMLResponse:
        return self.templates.TemplateResponse(
            request,
            name="pages/settings/profile.html",
            context={
                "request": request,
                "menu": await self.MenuService.get_menu_component(request),
            },
        )

    @Get("/fiat", response_class=HTMLResponse)
    @Shield.need(
        name="fiat",
        action="read",
        type="template",
        description="view fiat",
    )
    @enqueue_css(
        css_tag=str(
            Style(href="/app-static/css/app.css", type="text/css", media="all")
        ),
        position=CssSite.HEAD,
    )
    @enqueue_js(
        js_tag=str(Script(src="/app-static/ts/icons.js", type="module", defer=True)),
        position=Site.HEAD,
    )
    @enqueue_js(
        js_tag=str(
            Script(
                src="/app-static/ts/store/chinese-restaurant-store.js",
                type="module",
                defer=True,
            )
        ),
        position=Site.HEAD,
    )
    @enqueue_js(
        js_tag=str(
            Script(
                src="/app-static/ts/store/fiatStore.js",
                type="module",
                defer=True,
            )
        ),
        position=Site.HEAD,
    )
    @enqueue_js(
        js_tag=str(
            Script(
                src="/app-static/ts/pages/settings/fiat.js",
                type="module",
                defer=True,
            )
        ),
        position=Site.HEAD,
    )
    @CSRF()
    async def fiat(self, request: Request) -> HTMLResponse:
        return self.templates.TemplateResponse(
            request,
            name="pages/settings/fiat.html",
            context={
                "request": request,
                "menu": await self.MenuService.get_menu_component(request),
            },
        )

    @Get("/members", response_class=HTMLResponse)
    @Shield.need(
        name="members",
        action="read",
        type="template",
        description="view members",
    )
    @enqueue_css(
        css_tag=str(
            Style(href="/app-static/css/app.css", type="text/css", media="all")
        ),
        position=CssSite.HEAD,
    )
    @enqueue_js(
        js_tag=str(Script(src="/app-static/ts/icons.js", type="module", defer=True)),
        position=Site.HEAD,
    )
    @CSRF()
    async def members(self, request: Request) -> HTMLResponse:
        return self.templates.TemplateResponse(
            request,
            name="pages/settings/members.html",
            context={
                "request": request,
                "menu": await self.MenuService.get_menu_component(request),
            },
        )

    @Get("/notifications", response_class=HTMLResponse)
    @Shield.need(
        name="notifications",
        action="read",
        type="template",
        description="view notifications",
    )
    @enqueue_css(
        css_tag=str(
            Style(href="/app-static/css/app.css", type="text/css", media="all")
        ),
        position=CssSite.HEAD,
    )
    @enqueue_js(
        js_tag=str(Script(src="/app-static/ts/icons.js", type="module", defer=True)),
        position=Site.HEAD,
    )
    @CSRF()
    async def notifications(self, request: Request) -> HTMLResponse:
        return self.templates.TemplateResponse(
            request,
            name="pages/settings/notifications.html",
            context={
                "request": request,
                "menu": await self.MenuService.get_menu_component(request),
            },
        )

    @Get("/security", response_class=HTMLResponse)
    @Shield.need(
        name="security",
        action="read",
        type="template",
        description="view security",
    )
    @enqueue_css(
        css_tag=str(
            Style(href="/app-static/css/app.css", type="text/css", media="all")
        ),
        position=CssSite.HEAD,
    )
    @enqueue_js(
        js_tag=str(Script(src="/app-static/ts/icons.js", type="module", defer=True)),
        position=Site.HEAD,
    )
    @CSRF()
    async def security(self, request: Request) -> HTMLResponse:
        return self.templates.TemplateResponse(
            request,
            name="pages/settings/security.html",
            context={
                "request": request,
                "menu": await self.MenuService.get_menu_component(request),
            },
        )
