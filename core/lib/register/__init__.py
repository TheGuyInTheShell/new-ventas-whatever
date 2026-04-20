"""Exports públicos del paquete de registro de rutas."""

from core.lib.register.auto_router_api import auto_router_api
from core.lib.register.auto_router_templates import auto_router_templates
from core.lib.register.controller import Controller
from core.lib.register.exceptions import (
    ApiControllerMissingError,
    ControllerFileNotFoundWarning,
    DuplicateRouteHandlerError,
    TemplateControllerMissingError,
    TemplateFileNotFoundWarning,
)
from core.lib.register.template import Template
from core.lib.register.service import Service
from core.lib.register.partial import Partial

__all__: list[str] = [
    "auto_router_api",
    "auto_router_templates",
    "ApiControllerMissingError",
    "Controller",
    "ControllerFileNotFoundWarning",
    "DuplicateRouteHandlerError",
    "Template",
    "TemplateControllerMissingError",
    "TemplateFileNotFoundWarning",
    "Service",
    "Partial",
]
