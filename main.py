"""
Punto de entrada de la aplicación FastAPI.

Configura la aplicación y auto-registra las rutas de templates y API
usando la librería de auto-registro.
"""

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse

from core.lib.register.auto_router_api import auto_router_api
from core.lib.register.auto_router_templates import auto_router_templates
from core.lib.register.plugin_loader import plugin_lifespan
from core.lib.register.extension_loader import load_extensions
from core.lib.register.auto_router_sockets import auto_router_sockets
from core.lib.register.auto_router_partials import auto_router_partials
from core.lib.hooks.lifespan import on_app_init

# ---------------------------------------------------------------------------
# Inicialización de la aplicación FastAPI
# ---------------------------------------------------------------------------

app: FastAPI = FastAPI(
    title="FastAPI Template",
    lifespan=plugin_lifespan,
)


@on_app_init
def init_shield_permissions(app: FastAPI):
    from core.security.shield.shield import Shield
    from core.database import SessionAsync
    from src.modules.permissions.services import PermissionsService
    from src.modules.auth.guards import AuthGuardApi, AuthGuardApp

    perm_service = PermissionsService()
    Shield.scan(
        path="src/api",
        callback=perm_service.get_shield_sync_callback(sessionAsync=SessionAsync),
        context="API",
        resolver=AuthGuardApi(),
    )
    Shield.scan(
        path="src/app",
        callback=perm_service.get_shield_sync_callback(sessionAsync=SessionAsync),
        context="WEB",
        resolver=AuthGuardApp(),
    )


# Initial load of extensions (e.g. Middlewares)
load_extensions(app)

# ---------------------------------------------------------------------------
# Proveedores de templates (Jinja2) por módulo
# ---------------------------------------------------------------------------

app_templates: Jinja2Templates = Jinja2Templates(directory="src/app/web")


# ---------------------------------------------------------------------------
# Auto-registro de rutas
# ---------------------------------------------------------------------------

# App: prefix "" (raíz)
auto_router_templates(
    app=app,
    template_provider=app_templates,
    templates_controllers_path="src/app/templates",
    prefix="",
    statics_prefix="/app-static",
    statics_path="src/app/web/out",
)

auto_router_partials(
    app=app,
    template_provider=app_templates,
    partials_controllers_path="src/app/partials",
    prefix="/partials",
)

# API: prefix /api/v1
auto_router_api(
    app=app,
    controllers_path="src/api",
    prefix="/api/v1",
)


# ---------------------------------------------------------------------------
# Auto-registro de sockets
# ---------------------------------------------------------------------------

# Sockets: prefix "/ws"
auto_router_sockets(
    app=app,
    sockets_path="src/sockets",
    async_mode="asgi",
    cors_allowed_origins=[],
    path="/sio",
    logger=True,
    engineio_logger=True,
    allow_upgrades=True,
)


@app.get("/favicon.ico")
def favicon():
    return FileResponse("public/favicon.ico")
