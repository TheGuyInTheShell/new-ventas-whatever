"""
Punto de entrada de la aplicación FastAPI.

Configura la aplicación y auto-registra las rutas de templates
para los módulos admin y app usando la librería de auto-registro.

Ejemplo de uso de ``auto_router_templates`` para registrar
dos árboles de templates independientes, cada uno con su propio
proveedor de templates (Jinja2) y prefix HTTP.
"""

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

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
app_templates: Jinja2Templates = Jinja2Templates(directory="src/app/web")


# ---------------------------------------------------------------------------
# Auto-registro de rutas de templates para admin
# ---------------------------------------------------------------------------
# Estructura esperada:
#   src/admin/templates/template.py       → /admin/
#   src/admin/templates/dashboard/template.py → /admin/dashboard
#   src/admin/templates/dashboard/logs/template.py → /admin/dashboard/logs
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
#   src/app/templates/template.py         → /app/
#   src/app/templates/dashboard/template.py → /app/dashboard
# ---------------------------------------------------------------------------

auto_router_templates(
    app=app,
    template_provider=app_templates,
    templates_controllers_path="src/app/templates",
    prefix="",
)