"""Exports públicos del paquete de registro de rutas."""

from core.lib.register.auto_router_templates import auto_router_templates
from core.lib.register.exceptions import (
    DuplicateRouteHandlerError,
    TemplateControllerMissingError,
    TemplateFileNotFoundWarning,
)
from core.lib.register.template import Template

__all__: list[str] = [
    "auto_router_templates",
    "DuplicateRouteHandlerError",
    "Template",
    "TemplateControllerMissingError",
    "TemplateFileNotFoundWarning",
]