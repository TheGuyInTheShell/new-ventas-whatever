"""
Auto-registro recursivo de rutas de partials (fragmentos HTML) para FastAPI.

Escanea recursivamente un árbol de directorios buscando archivos ``partial.py``
que contengan clases heredando de ``Partial``. Para cada clase encontrada,
extrae los métodos decorados con ``@Get``, ``@Post``, etc., y los registra
como rutas en la aplicación FastAPI.

Uso típico::

    from fastapi import FastAPI
    from core.lib.register.auto_router_partials import auto_router_partials

    app = FastAPI()
    app_templates = Jinja2Templates(directory="src/app/web")

    auto_router_partials(
        app=app,
        template_provider=app_templates,
        partials_controllers_path="src/app/partials",
        prefix="/partials",
    )
"""

import inspect
import os
import warnings
from importlib import import_module
from typing import Any, Dict, List, Optional, Type

from fastapi import FastAPI
from fastapi.routing import APIRouter

from core.lib.decorators.http_methods import (
    HTTPMethod,
    RouteDefinition,
    RouteRegistry,
    route_registry,
)
from core.lib.register.exceptions import (
    PartialControllerMissingError,
    PartialFileNotFoundWarning,
)
from core.lib.register.partial import Partial


# ---------------------------------------------------------------------------
# Constantes internas
# ---------------------------------------------------------------------------

_IGNORED_DIRECTORIES: frozenset[str] = frozenset({
    "__pycache__",
    ".git",
    ".mypy_cache",
    "node_modules",
})

_PARTIAL_MODULE_NAME: str = "partial"
_PARTIAL_FILE_NAME: str = f"{_PARTIAL_MODULE_NAME}.py"


# ---------------------------------------------------------------------------
# Funciones auxiliares privadas
# ---------------------------------------------------------------------------


def _normalize_path_to_module(filesystem_path: str) -> str:
    """Convierte una ruta del filesystem a un import path de Python."""
    normalized: str = filesystem_path.replace("\\", "/").rstrip("/")
    return normalized.replace("/", ".")


def _compute_http_route(
    directory_path: str,
    base_path: str,
) -> str:
    """Calcula la ruta HTTP relativa de un directorio respecto a la base."""
    normalized_dir: str = directory_path.replace("\\", "/").rstrip("/")
    normalized_base: str = base_path.replace("\\", "/").rstrip("/")

    relative_path: str = normalized_dir[len(normalized_base):].strip("/")

    if not relative_path:
        return "/"

    return f"/{relative_path}"


def _find_partial_classes(
    module: Any,
) -> List[Type[Partial]]:
    """Busca todas las clases que heredan de Partial en un módulo."""
    partial_classes: List[Type[Partial]] = []

    for _name, obj in inspect.getmembers(module, predicate=inspect.isclass):
        is_partial_subclass: bool = (
            issubclass(obj, Partial) and obj is not Partial
        )

        if is_partial_subclass:
            partial_classes.append(obj)

    return partial_classes


def _extract_route_definitions(
    partial_class: Type[Partial],
) -> List[RouteDefinition]:
    """Extrae todas las definiciones de ruta de los métodos de una clase Partial."""
    route_definitions: List[RouteDefinition] = []

    for attribute_name in dir(partial_class):
        if attribute_name.startswith("_"):
            continue

        attribute: Any = getattr(partial_class, attribute_name, None)

        if attribute is None:
            continue

        route_definition: Optional[RouteDefinition] = getattr(
            attribute, "__route_definition__", None
        )

        if route_definition is not None:
            route_definitions.append(route_definition)

    return route_definitions


def _build_router_from_definitions(
    partial_instance: Partial,
    route_definitions: List[RouteDefinition],
    class_name: str,
    registry: RouteRegistry,
) -> APIRouter:
    """Construye un APIRouter de FastAPI a partir de definiciones de ruta."""
    router: APIRouter = APIRouter()

    http_method_to_router_method: Dict[HTTPMethod, str] = {
        HTTPMethod.GET: "get",
        HTTPMethod.POST: "post",
        HTTPMethod.DELETE: "delete",
        HTTPMethod.PUT: "put",
        HTTPMethod.PATCH: "patch",
        HTTPMethod.HEAD: "head",
        HTTPMethod.OPTIONS: "options",
    }

    for definition in route_definitions:
        registry.register(
            class_name=class_name,
            definition=definition,
        )

        router_method_name: str = http_method_to_router_method[definition.http_method]
        router_method: Any = getattr(router, router_method_name)

        bound_handler: Any = getattr(partial_instance, definition.handler_name)

        route_paths: List[str] = (
            definition.route_path
            if isinstance(definition.route_path, list)
            else [definition.route_path]
        )

        for single_path in route_paths:
            router_method(single_path, **definition.kwargs)(bound_handler)

    return router


# ---------------------------------------------------------------------------
# Función pública principal
# ---------------------------------------------------------------------------


def auto_router_partials(
    app: FastAPI,
    template_provider: Any,
    partials_controllers_path: str,
    prefix: str = "",
) -> FastAPI:
    """Auto-registra rutas de partials escaneando recursivamente un árbol de directorios.

    Args:
        app: Instancia de la aplicación FastAPI.
        template_provider: Instancia del motor de renderizado de templates.
        partials_controllers_path: Ruta del directorio raíz de partials.
        prefix: Prefijo HTTP para todas las rutas registradas.

    Returns:
        La misma instancia de ``FastAPI``.
    """
    normalized_base_path: str = partials_controllers_path.replace("\\", "/").rstrip("/")

    for current_root, subdirectories, files in os.walk(normalized_base_path):
        subdirectories[:] = [
            directory_name
            for directory_name in subdirectories
            if directory_name not in _IGNORED_DIRECTORIES
        ]

        normalized_root: str = current_root.replace("\\", "/").rstrip("/")

        if _PARTIAL_FILE_NAME not in files:
            is_root_directory: bool = normalized_root == normalized_base_path
            if not is_root_directory:
                warnings.warn(
                    PartialFileNotFoundWarning(directory_path=normalized_root),
                    stacklevel=2,
                )
            continue

        module_import_path: str = (
            f"{_normalize_path_to_module(normalized_root)}.{_PARTIAL_MODULE_NAME}"
        )
        http_route: str = _compute_http_route(
            directory_path=normalized_root,
            base_path=normalized_base_path,
        )

        imported_module: Any = import_module(module_import_path)
        partial_classes: List[Type[Partial]] = _find_partial_classes(imported_module)

        if not partial_classes:
            partial_file_full_path: str = os.path.join(
                normalized_root, _PARTIAL_FILE_NAME
            )
            raise PartialControllerMissingError(
                partial_file_path=partial_file_full_path,
                module_path=module_import_path,
            )

        for partial_class in partial_classes:
            class_full_name: str = (
                f"{module_import_path}.{partial_class.__name__}"
            )

            partial_instance: Partial = partial_class(
                template_provider=template_provider,
            )

            route_definitions: List[RouteDefinition] = _extract_route_definitions(
                partial_class=partial_class,
            )

            if not route_definitions:
                continue

            class_router: APIRouter = _build_router_from_definitions(
                partial_instance=partial_instance,
                route_definitions=route_definitions,
                class_name=class_full_name,
                registry=route_registry,
            )

            full_prefix: str
            if http_route == "/":
                full_prefix = prefix if prefix else ""
            else:
                full_prefix = f"{prefix}{http_route}" if prefix else http_route

            tag_label: str = (
                http_route.strip("/").replace("/", " - ") or "root"
            )
            app.include_router(
                class_router,
                prefix=full_prefix,
                tags=[f"view - partial - {tag_label}"],
            )

            print(
                f"[auto_router_partials] Registered: "
                f"class='{partial_class.__name__}' "
                f"prefix='{full_prefix}' "
                f"routes={len(route_definitions)} "
                f"module='{module_import_path}'"
            )

    return app
