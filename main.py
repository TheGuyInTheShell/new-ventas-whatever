"""
Punto de entrada de la aplicación FastAPI.

Configura la aplicación y auto-registra las rutas de templates y API
usando la librería de auto-registro.

Ejemplo de uso de ``auto_router_templates`` y ``auto_router_api`` para
registrar árboles de templates y controllers API independientes.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core.lib.consts.template import CONTEXT_INJECTABLE
from core.lib.register.auto_router_api import auto_router_api
from core.lib.register.auto_router_templates import auto_router_templates


# ---------------------------------------------------------------------------
# Inicialización de la aplicación FastAPI
# ---------------------------------------------------------------------------

app: FastAPI = FastAPI(
    title="FastAPI Template",
)


# ---------------------------------------------------------------------------
# Proveedores de templates (Jinja2) por módulo
# ---------------------------------------------------------------------------

admin_templates: Jinja2Templates = Jinja2Templates(directory="src/admin/web")
admin_templates.env.globals["_injectable"] = CONTEXT_INJECTABLE

app_templates: Jinja2Templates = Jinja2Templates(directory="src/app/web")
app_templates.env.globals["_injectable"] = CONTEXT_INJECTABLE


# ---------------------------------------------------------------------------
# Auto-registro de rutas de templates para admin
# ---------------------------------------------------------------------------
# Estructura esperada:
#   src/admin/templates/template.py       → /admin/
#   src/admin/templates/dashboard/template.py → /admin/dashboard
# ---------------------------------------------------------------------------

auto_router_templates(
    app=app,
    template_provider=admin_templates,
    templates_controllers_path="src/admin/templates",
    prefix="/admin",
)


# ---------------------------------------------------------------------------
# Auto-registro de rutas de templates para app
# ---------------------------------------------------------------------------
# Estructura esperada:
#   src/app/templates/template.py         → /
#   src/app/templates/dashboard/template.py → /dashboard
# ---------------------------------------------------------------------------

auto_router_templates(
    app=app,
    template_provider=app_templates,
    templates_controllers_path="src/app/templates",
    prefix="",
)


# ---------------------------------------------------------------------------
# Auto-registro de rutas de API
# ---------------------------------------------------------------------------
# Estructura esperada:
#   src/api/health/controller.py → /api/v1/health
#   src/api/users/controller.py  → /api/v1/users
#   src/api/auth/controller.py   → /api/v1/auth
#
# Directorios ignorados automáticamente:
#   schemas/, services/, models/, utils/, types/, middlewares/, dependencies/
# ---------------------------------------------------------------------------

auto_router_api(
    app=app,
    controllers_path="src/api",
    prefix="/api/v1",
)