"""
Auto-registro recursivo de rutas de templates para FastAPI.

Escanea recursivamente un árbol de directorios buscando archivos ``template.py``
que contengan clases heredando de ``Template``. Para cada clase encontrada,
extrae los métodos decorados con ``@Get``, ``@Post``, etc., y los registra
como rutas en la aplicación FastAPI.

Convención de rutas HTTP basada en la estructura de directorios:

- Directorio raíz del árbol → ``/`` (raíz del prefix)
- ``dashboard/`` → ``/dashboard``
- ``dashboard/settings/`` → ``/dashboard/settings``

Convención de archivos:

- Cada directorio que desee exponer rutas DEBE contener un ``template.py``
- El ``template.py`` DEBE contener al menos una clase que herede de ``Template``
- Si un directorio no contiene ``template.py``, se emite un warning

Uso típico::

    from fastapi import FastAPI
    from fastapi.templating import Jinja2Templates
    from core.lib.register.auto_router_templates import auto_router_templates

    app = FastAPI()
    admin_templates = Jinja2Templates(directory="src/admin/web")

    auto_router_templates(
        app=app,
        template_provider=admin_templates,
        templates_controllers_path="src/admin/templates",
        prefix="/admin",
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
    TemplateControllerMissingError,
    TemplateFileNotFoundWarning,
)
from core.lib.register.template import Template


# ---------------------------------------------------------------------------
# Constantes internas
# ---------------------------------------------------------------------------

_IGNORED_DIRECTORIES: frozenset[str] = frozenset({
    "__pycache__",
    ".git",
    ".mypy_cache",
    "node_modules",
})

_TEMPLATE_MODULE_NAME: str = "template"
_TEMPLATE_FILE_NAME: str = f"{_TEMPLATE_MODULE_NAME}.py"


# ---------------------------------------------------------------------------
# Funciones auxiliares privadas
# ---------------------------------------------------------------------------


def _normalize_path_to_module(filesystem_path: str) -> str:
    """Convierte una ruta del filesystem a un import path de Python.

    Reemplaza separadores de directorio (``/`` y ``\\``) por puntos (``.``).

    Args:
        filesystem_path: Ruta del filesystem. Ejemplo: ``src/admin/templates/dashboard``.

    Returns:
        Import path de Python. Ejemplo: ``src.admin.templates.dashboard``.
    """
    normalized: str = filesystem_path.replace("\\", "/").rstrip("/")
    return normalized.replace("/", ".")


def _compute_http_route(
    directory_path: str,
    base_path: str,
) -> str:
    """Calcula la ruta HTTP relativa de un directorio respecto a la base.

    La ruta HTTP se deriva de la posición relativa del directorio dentro
    del árbol de templates.

    Args:
        directory_path: Ruta completa del directorio. Ejemplo: ``src/admin/templates/dashboard``.
        base_path: Ruta base del árbol de templates. Ejemplo: ``src/admin/templates``.

    Returns:
        Ruta HTTP relativa. Ejemplo: ``/dashboard``.
        Para el directorio raíz, retorna ``/``.

    Examples:
        >>> _compute_http_route("src/admin/templates", "src/admin/templates")
        "/"
        >>> _compute_http_route("src/admin/templates/dashboard", "src/admin/templates")
        "/dashboard"
        >>> _compute_http_route("src/admin/templates/dashboard/settings", "src/admin/templates")
        "/dashboard/settings"
    """
    normalized_dir: str = directory_path.replace("\\", "/").rstrip("/")
    normalized_base: str = base_path.replace("\\", "/").rstrip("/")

    relative_path: str = normalized_dir[len(normalized_base):].strip("/")

    if not relative_path:
        return "/"

    return f"/{relative_path}"


def _find_template_classes(
    module: Any,
) -> List[Type[Template]]:
    """Busca todas las clases que heredan de Template en un módulo.

    Solo retorna clases que son subclases directas o indirectas de
    ``Template``, excluyendo la propia clase ``Template``.

    Args:
        module: Módulo Python importado para inspeccionar.

    Returns:
        Lista de clases que heredan de Template encontradas en el módulo.
    """
    template_classes: List[Type[Template]] = []

    for _name, obj in inspect.getmembers(module, predicate=inspect.isclass):
        is_template_subclass: bool = (
            issubclass(obj, Template) and obj is not Template
        )

        if is_template_subclass:
            template_classes.append(obj)

    return template_classes


def _extract_route_definitions(
    template_class: Type[Template],
) -> List[RouteDefinition]:
    """Extrae todas las definiciones de ruta de los métodos de una clase Template.

    Inspecciona todos los atributos de la clase buscando métodos que tengan
    el atributo ``__route_definition__`` (seteado por los decoradores HTTP).

    Args:
        template_class: Clase que hereda de Template a inspeccionar.

    Returns:
        Lista de definiciones de ruta encontradas en los métodos de la clase.
    """
    route_definitions: List[RouteDefinition] = []

    for attribute_name in dir(template_class):
        # Ignorar atributos dunder y privados
        if attribute_name.startswith("_"):
            continue

        attribute: Any = getattr(template_class, attribute_name, None)

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
    template_instance: Template,
    route_definitions: List[RouteDefinition],
    class_name: str,
    registry: RouteRegistry,
) -> APIRouter:
    """Construye un APIRouter de FastAPI a partir de definiciones de ruta.

    Registra cada definición en el ``RouteRegistry`` para validar unicidad,
    y luego crea las rutas correspondientes en el ``APIRouter``.

    Args:
        template_instance: Instancia de la clase Template con el proveedor inyectado.
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

        # Obtener el handler bound a la instancia del template
        bound_handler: Any = getattr(template_instance, definition.handler_name)

        # Procesar rutas (puede ser string o lista de strings)
        route_paths: List[str] = (
            definition.route_path
            if isinstance(definition.route_path, list)
            else [definition.route_path]
        )

        for single_path in route_paths:
            router_method(single_path, **definition.kwargs)(bound_handler)

    return router


def _build_statics_route(
    app: FastAPI, 
    statics_prefix: str = "", 
    statics_path: str = ""
) -> None:
    """Monta un directorio para servir archivos estáticos."""
    if not (statics_prefix and statics_path):
        return

    if not os.path.isdir(statics_path):
        warnings.warn(
            f"Directorio de estáticos no encontrado o no es un directorio válido: {statics_path}",
            stacklevel=2
        )
        return

    # Usamos import inline de 'fastapi.staticfiles' para evitar errores si no
    # está instalado o no se requiere usar archivos estáticos en el entorno.
    from fastapi.staticfiles import StaticFiles
    
    route_name: str = statics_prefix.strip("/").replace("/", "_") or "static"
    app.mount(
        statics_prefix, 
        StaticFiles(directory=statics_path), 
        name=route_name
    )

# ---------------------------------------------------------------------------
# Función pública principal
# ---------------------------------------------------------------------------


def auto_router_templates(
    app: FastAPI,
    template_provider: Any,
    templates_controllers_path: str,
    prefix: str = "",
    statics_prefix: str = "",
    statics_path: str = ""
) -> FastAPI:
    """Auto-registra rutas de templates escaneando recursivamente un árbol de directorios.

    Recorre el árbol de directorios especificado por ``templates_controllers_path``,
    buscando archivos ``template.py`` que contengan clases heredando de ``Template``.
    Para cada clase encontrada, extrae los métodos decorados y los registra como
    rutas en la aplicación FastAPI.

    La ruta HTTP se calcula automáticamente a partir de la posición del directorio
    dentro del árbol:

    - Raíz (``templates_controllers_path``) → ``{prefix}/``
    - ``dashboard/`` → ``{prefix}/dashboard``
    - ``dashboard/settings/`` → ``{prefix}/dashboard/settings``

    Args:
        app: Instancia de la aplicación FastAPI donde se registrarán las rutas.
        template_provider: Instancia del motor de renderizado de templates
            (e.g. ``Jinja2Templates``, ``MakoTemplates``). Se inyecta en cada
            clase Template encontrada.
        templates_controllers_path: Ruta del directorio raíz del árbol de templates.
            Ejemplo: ``"src/admin/templates"``.
        prefix: Prefijo HTTP para todas las rutas registradas.
            Ejemplo: ``"/admin"`` → las rutas serán ``/admin/``, ``/admin/dashboard``, etc.

    Returns:
        La misma instancia de ``FastAPI`` con las rutas registradas.

    Raises:
        TemplateControllerMissingError: Si un ``template.py`` no contiene
            ninguna clase que herede de ``Template``.
        DuplicateRouteHandlerError: Si se detectan handlers duplicados
            (mismo nombre + mismo método HTTP).

    Warnings:
        TemplateFileNotFoundWarning: Si un directorio dentro del árbol no
            contiene ``template.py``.
    """
    normalized_base_path: str = templates_controllers_path.replace("\\", "/").rstrip("/")

    # Registrar rutas de archivos estáticos si están definidas
    _build_statics_route(
        app=app,
        statics_prefix=statics_prefix,
        statics_path=statics_path
    )

    for current_root, subdirectories, files in os.walk(normalized_base_path):
        # Filtrar directorios ignorados para evitar recursión innecesaria
        subdirectories[:] = [
            directory_name
            for directory_name in subdirectories
            if directory_name not in _IGNORED_DIRECTORIES
        ]

        normalized_root: str = current_root.replace("\\", "/").rstrip("/")

        # -----------------------------------------------------------------
        # Verificar si el directorio actual contiene template.py
        # -----------------------------------------------------------------
        if _TEMPLATE_FILE_NAME not in files:
            # La raíz del árbol no requiere template.py obligatoriamente
            is_root_directory: bool = normalized_root == normalized_base_path

            if not is_root_directory:
                warnings.warn(
                    TemplateFileNotFoundWarning(directory_path=normalized_root),
                    stacklevel=2,
                )
            continue

        # -----------------------------------------------------------------
        # Calcular el import path del módulo y la ruta HTTP
        # -----------------------------------------------------------------
        module_import_path: str = (
            f"{_normalize_path_to_module(normalized_root)}.{_TEMPLATE_MODULE_NAME}"
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
        # Buscar clases que hereden de Template
        # -----------------------------------------------------------------
        template_classes: List[Type[Template]] = _find_template_classes(imported_module)

        if not template_classes:
            template_file_full_path: str = os.path.join(
                normalized_root, _TEMPLATE_FILE_NAME
            )
            raise TemplateControllerMissingError(
                template_file_path=template_file_full_path,
                module_path=module_import_path,
            )

        # -----------------------------------------------------------------
        # Procesar cada clase Template encontrada
        # -----------------------------------------------------------------
        for template_class in template_classes:
            class_full_name: str = (
                f"{module_import_path}.{template_class.__name__}"
            )

            # Instanciar la clase con el proveedor de templates
            template_instance: Template = template_class(
                template_provider=template_provider,
            )

            # Extraer definiciones de ruta de los métodos decorados
            route_definitions: List[RouteDefinition] = _extract_route_definitions(
                template_class=template_class,
            )

            if not route_definitions:
                continue

            # Construir router y registrar rutas (con validación de duplicados)
            class_router: APIRouter = _build_router_from_definitions(
                template_instance=template_instance,
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
                tags=[f"view - {tag_label}"],
            )

            print(
                f"[auto_router_templates] Registered: "
                f"class='{template_class.__name__}' "
                f"prefix='{full_prefix}' "
                f"routes={len(route_definitions)} "
                f"module='{module_import_path}'"
            )

    return app
