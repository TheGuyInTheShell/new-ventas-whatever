"""
Punto de entrada de la aplicación FastAPI.

Configura la aplicación y auto-registra las rutas de templates y API
usando la librería de auto-registro.
"""

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

from core.lib.consts.template import CONTEXT_INJECTABLE
from core.lib.register.auto_router_api import auto_router_api
from core.lib.register.auto_router_templates import auto_router_templates
from core.lib.register.plugin_loader import plugin_lifespan
from core.lib.register.extension_loader import load_extensions
from core.lib.register.auto_router_sockets import auto_router_sockets

# ---------------------------------------------------------------------------
# Inicialización de la aplicación FastAPI
# ---------------------------------------------------------------------------

app: FastAPI = FastAPI(
    title="FastAPI Template",
    lifespan=plugin_lifespan,
)


# Initial load of extensions (e.g. Middlewares)
load_extensions(app)

# ---------------------------------------------------------------------------
# Proveedores de templates (Jinja2) por módulo
# ---------------------------------------------------------------------------

app_templates: Jinja2Templates = Jinja2Templates(directory="src/app/web")
app_templates.env.globals["_injectable"] = CONTEXT_INJECTABLE
app_templates.env.globals["STATIC_URL"] = "/app-static"


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
