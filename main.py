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

admin_templates: Jinja2Templates = Jinja2Templates(directory="src/admin/web")
admin_templates.env.globals["_injectable"] = CONTEXT_INJECTABLE
admin_templates.env.globals["STATIC_URL"] = "/admin-static"

app_templates: Jinja2Templates = Jinja2Templates(directory="src/app/web")
app_templates.env.globals["_injectable"] = CONTEXT_INJECTABLE
app_templates.env.globals["STATIC_URL"] = "/app-static"


# ---------------------------------------------------------------------------
# Auto-registro de rutas
# ---------------------------------------------------------------------------

# Admin: prefix /admin
auto_router_templates(
    app=app,
    template_provider=admin_templates,
    templates_controllers_path="src/admin/templates",
    prefix="/admin",
    statics_prefix="/admin-static",
    statics_path="src/admin/web/out",
)

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