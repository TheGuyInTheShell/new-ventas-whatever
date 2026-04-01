"""
Auto-registro recursivo de rutas de API para FastAPI.

Escanea recursivamente un árbol de directorios buscando archivos ``controller.py``
que contengan clases heredando de ``Controller``. Para cada clase encontrada,
extrae los métodos decorados con ``@Get``, ``@Post``, etc., y los registra
como rutas en la aplicación FastAPI.

Convención de rutas HTTP basada en la estructura de directorios:

- Directorio raíz del árbol → ``/`` (raíz del prefix)
- ``users/`` → ``/users``
- ``users/roles/`` → ``/users/roles``

Convención de archivos:

- Cada directorio que desee exponer endpoints DEBE contener un ``controller.py``
- El ``controller.py`` DEBE contener al menos una clase que herede de ``Controller``
- Si un directorio no contiene ``controller.py``, se emite un warning
- Directorios auxiliares (schemas, services, models, etc.) se ignoran automáticamente

Uso típico::

    from fastapi import FastAPI
    from core.lib.register.auto_router_api import auto_router_api

    app = FastAPI()

    auto_router_api(
        app=app,
        controllers_path="src/api",
        prefix="/api/v1",
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
from core.lib.register.controller import Controller
from core.lib.register.exceptions import (
    ApiControllerMissingError,
    ControllerFileNotFoundWarning,
)


# ---------------------------------------------------------------------------
# Constantes internas
# ---------------------------------------------------------------------------

_IGNORED_DIRECTORIES: frozenset[str] = frozenset({
    "__pycache__",
    ".git",
    ".mypy_cache",
    "node_modules",
    "schemas",
    "services",
    "models",
    "types",
    "utils",
    "middlewares",
    "dependencies",
})

_CONTROLLER_MODULE_NAME: str = "controller"
_CONTROLLER_FILE_NAME: str = f"{_CONTROLLER_MODULE_NAME}.py"


# ---------------------------------------------------------------------------
# Funciones auxiliares privadas
# ---------------------------------------------------------------------------


def _normalize_path_to_module(filesystem_path: str) -> str:
    """Convierte una ruta del filesystem a un import path de Python.

    Reemplaza separadores de directorio (``/`` y ``\\``) por puntos (``.``).

    Args:
        filesystem_path: Ruta del filesystem. Ejemplo: ``src/api/users``.

    Returns:
        Import path de Python. Ejemplo: ``src.api.users``.
    """
    normalized: str = filesystem_path.replace("\\", "/").rstrip("/")
    return normalized.replace("/", ".")


def _compute_http_route(
    directory_path: str,
    base_path: str,
) -> str:
    """Calcula la ruta HTTP relativa de un directorio respecto a la base.

    La ruta HTTP se deriva de la posición relativa del directorio dentro
    del árbol de controllers de API.

    Args:
        directory_path: Ruta completa del directorio. Ejemplo: ``src/api/users``.
        base_path: Ruta base del árbol de API. Ejemplo: ``src/api``.

    Returns:
        Ruta HTTP relativa. Ejemplo: ``/users``.
        Para el directorio raíz, retorna ``/``.

    Examples:
        >>> _compute_http_route("src/api", "src/api")
        "/"
        >>> _compute_http_route("src/api/users", "src/api")
        "/users"
        >>> _compute_http_route("src/api/users/roles", "src/api")
        "/users/roles"
    """
    normalized_dir: str = directory_path.replace("\\", "/").rstrip("/")
    normalized_base: str = base_path.replace("\\", "/").rstrip("/")

    relative_path: str = normalized_dir[len(normalized_base):].strip("/")

    if not relative_path:
        return "/"

    return f"/{relative_path}"


def _find_controller_classes(
    module: Any,
) -> List[Type[Controller]]:
    """Busca todas las clases que heredan de Controller en un módulo.

    Solo retorna clases que son subclases directas o indirectas de
    ``Controller``, excluyendo la propia clase ``Controller``.

    Args:
        module: Módulo Python importado para inspeccionar.

    Returns:
        Lista de clases que heredan de Controller encontradas en el módulo.
    """
    controller_classes: List[Type[Controller]] = []

    for _name, obj in inspect.getmembers(module, predicate=inspect.isclass):
        is_controller_subclass: bool = (
            issubclass(obj, Controller) and obj is not Controller
        )

        if is_controller_subclass:
            controller_classes.append(obj)

    return controller_classes


def _extract_route_definitions(
    controller_class: Type[Controller],
) -> List[RouteDefinition]:
    """Extrae todas las definiciones de ruta de los métodos de una clase Controller.

    Inspecciona todos los atributos de la clase buscando métodos que tengan
    el atributo ``__route_definition__`` (seteado por los decoradores HTTP).

    Args:
        controller_class: Clase que hereda de Controller a inspeccionar.

    Returns:
        Lista de definiciones de ruta encontradas en los métodos de la clase.
    """
    route_definitions: List[RouteDefinition] = []

    for attribute_name in dir(controller_class):
        # Ignorar atributos dunder y privados
        if attribute_name.startswith("_"):
            continue

        attribute: Any = getattr(controller_class, attribute_name, None)

        if attribute is None:
            continue

        # Verificar si el atributo tiene metadata de ruta
        route_definition: Optional[RouteDefinition] = getattr(
            attribute, "__route_definition__", None
        )

        if route_definition is not None:
            route_definitions.append(route_definition)

    return route_definitions


def _build_router_from_definitions(
    controller_instance: Controller,
    route_definitions: List[RouteDefinition],
    class_name: str,
    registry: RouteRegistry,
) -> APIRouter:
    """Construye un APIRouter de FastAPI a partir de definiciones de ruta.

    Registra cada definición en el ``RouteRegistry`` para validar unicidad,
    y luego crea las rutas correspondientes en el ``APIRouter``.

    Args:
        controller_instance: Instancia de la clase Controller.
        route_definitions: Lista de definiciones de ruta a registrar.
        class_name: Nombre completo de la clase para el registro.
        registry: Instancia del registro de rutas para validación.

    Returns:
        APIRouter configurado con todas las rutas de la clase.

    Raises:
        DuplicateRouteHandlerError: Si se detecta un handler duplicado.
    """
    router: APIRouter = APIRouter()

    # Mapeo de HTTPMethod a métodos de APIRouter
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
        # Validar unicidad en el registro
        registry.register(
            class_name=class_name,
            definition=definition,
        )

        # Obtener el método correspondiente del router (router.get, router.post, etc.)
        router_method_name: str = http_method_to_router_method[definition.http_method]
        router_method: Any = getattr(router, router_method_name)

        # Obtener el handler bound a la instancia del controller
        bound_handler: Any = getattr(controller_instance, definition.handler_name)

        # Procesar rutas (puede ser string o lista de strings)
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


def auto_router_api(
    app: FastAPI,
    controllers_path: str,
    prefix: str = "/api/v1",
) -> FastAPI:
    """Auto-registra rutas de API escaneando recursivamente un árbol de directorios.

    Recorre el árbol de directorios especificado por ``controllers_path``,
    buscando archivos ``controller.py`` que contengan clases heredando de
    ``Controller``. Para cada clase encontrada, extrae los métodos decorados
    y los registra como rutas en la aplicación FastAPI.

    La ruta HTTP se calcula automáticamente a partir de la posición del directorio
    dentro del árbol:

    - Raíz (``controllers_path``) → ``{prefix}/``
    - ``users/`` → ``{prefix}/users``
    - ``users/roles/`` → ``{prefix}/users/roles``

    Directorios auxiliares como ``schemas``, ``services``, ``models``, ``utils``,
    ``types``, ``middlewares`` y ``dependencies`` se ignoran automáticamente.

    Args:
        app: Instancia de la aplicación FastAPI donde se registrarán las rutas.
        controllers_path: Ruta del directorio raíz del árbol de controllers.
            Ejemplo: ``"src/api"``.
        prefix: Prefijo HTTP para todas las rutas registradas.
            Ejemplo: ``"/api/v1"`` → las rutas serán ``/api/v1/users``, etc.

    Returns:
        La misma instancia de ``FastAPI`` con las rutas registradas.

    Raises:
        ApiControllerMissingError: Si un ``controller.py`` no contiene
            ninguna clase que herede de ``Controller``.
        DuplicateRouteHandlerError: Si se detectan handlers duplicados
            (mismo nombre + mismo método HTTP).

    Warnings:
        ControllerFileNotFoundWarning: Si un directorio dentro del árbol no
            contiene ``controller.py``.
    """
    normalized_base_path: str = controllers_path.replace("\\", "/").rstrip("/")

    for current_root, subdirectories, files in os.walk(normalized_base_path):
        # Filtrar directorios ignorados para evitar recursión innecesaria
        subdirectories[:] = [
            directory_name
            for directory_name in subdirectories
            if directory_name not in _IGNORED_DIRECTORIES
        ]

        normalized_root: str = current_root.replace("\\", "/").rstrip("/")

        # -----------------------------------------------------------------
        # Verificar si el directorio actual contiene controller.py
        # -----------------------------------------------------------------
        if _CONTROLLER_FILE_NAME not in files:
            # La raíz del árbol no requiere controller.py obligatoriamente
            is_root_directory: bool = normalized_root == normalized_base_path

            if not is_root_directory:
                warnings.warn(
                    ControllerFileNotFoundWarning(directory_path=normalized_root),
                    stacklevel=2,
                )
            continue

        # -----------------------------------------------------------------
        # Calcular el import path del módulo y la ruta HTTP
        # -----------------------------------------------------------------
        module_import_path: str = (
            f"{_normalize_path_to_module(normalized_root)}.{_CONTROLLER_MODULE_NAME}"
        )
        http_route: str = _compute_http_route(
            directory_path=normalized_root,
            base_path=normalized_base_path,
        )

        # -----------------------------------------------------------------
        # Importar el módulo dinámicamente
        # -----------------------------------------------------------------
        imported_module: Any = import_module(module_import_path)

        # -----------------------------------------------------------------
        # Buscar clases que hereden de Controller
        # -----------------------------------------------------------------
        controller_classes: List[Type[Controller]] = _find_controller_classes(
            imported_module
        )

        if not controller_classes:
            controller_file_full_path: str = os.path.join(
                normalized_root, _CONTROLLER_FILE_NAME
            )
            raise ApiControllerMissingError(
                controller_file_path=controller_file_full_path,
                module_path=module_import_path,
            )

        # -----------------------------------------------------------------
        # Procesar cada clase Controller encontrada
        # -----------------------------------------------------------------
        for controller_class in controller_classes:
            class_full_name: str = (
                f"{module_import_path}.{controller_class.__name__}"
            )

            # Instanciar la clase controller (sin dependencias de template)
            controller_instance: Controller = controller_class()

            # Extraer definiciones de ruta de los métodos decorados
            route_definitions: List[RouteDefinition] = _extract_route_definitions(
                controller_class=controller_class,
            )

            if not route_definitions:
                continue

            # Construir router y registrar rutas (con validación de duplicados)
            class_router: APIRouter = _build_router_from_definitions(
                controller_instance=controller_instance,
                route_definitions=route_definitions,
                class_name=class_full_name,
                registry=route_registry,
            )

            # Calcular el prefix completo para esta ruta
            full_prefix: str
            if http_route == "/":
                full_prefix = prefix if prefix else ""
            else:
                full_prefix = f"{prefix}{http_route}" if prefix else http_route

            # Incluir el router en la aplicación FastAPI
            tag_label: str = (
                http_route.strip("/").replace("/", " - ") or "root"
            )
            app.include_router(
                class_router,
                prefix=full_prefix,
                tags=[f"api - {tag_label}"],
            )

            print(
                f"[auto_router_api] Registered: "
                f"class='{controller_class.__name__}' "
                f"prefix='{full_prefix}' "
                f"routes={len(route_definitions)} "
                f"module='{module_import_path}'"
            )

    return app