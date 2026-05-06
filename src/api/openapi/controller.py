"""
Controller para los endpoints custom de documentación de la API (Swagger/Redoc/OpenAPI).

Estructura de directorios → Ruta HTTP:
    src/api/openapi/controller.py → /api/v1/openapi

Nota: Se usa `Request` para acceder a la instancia `app` mediante `request.app`,
ya que FastAPI trataría `app: FastAPI` como un query param Pydantic inválido.
"""

from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse

from core.lib.decorators import Get
from core.lib.register import Controller
from core.security.shield import Shield


@Shield.register(context="Openapi module")
class DocController(Controller):

    @Get("/docs", include_in_schema=False, response_class=HTMLResponse)
    @Shield.need(
        name="docs",
        action="read",
        type="endpoint",
        description="Permite solicitar el schema de la API.",
    )
    async def custom_swagger_ui_html(self):
        app = self.app
        prefix = self.prefix
        return get_swagger_ui_html(
            openapi_url=f"{prefix}/openapi/openapi.json",
            title=app.title + " - Docs",
        )

    @Get(
        "/redoc",
        include_in_schema=False,
        response_class=HTMLResponse,
    )
    @Shield.need(
        name="redoc",
        action="read",
        type="endpoint",
        description="Permite solicitar el schema de la API.",
    )
    async def custom_redoc_html(self):
        app = self.app
        prefix = self.prefix
        return get_redoc_html(
            openapi_url=f"{prefix}/openapi/openapi.json",
            title=app.title + " - Redoc",
        )

    @Get("/openapi.json", include_in_schema=False)
    @Shield.need(
        name="openapi",
        action="read",
        type="endpoint",
        description="Permite solicitar el schema de la API.",
    )
    async def custom_openapi(self):
        app = self.app
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        app.openapi_schema = openapi_schema
        return app.openapi_schema
