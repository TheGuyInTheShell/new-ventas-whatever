"""
Decoradores HTTP para el sistema de auto-registro de rutas.

Proporciona decoradores para todos los métodos HTTP estándar (@Get, @Post, etc.)
que almacenan metadata de la ruta en el método decorado. Cada decorador crea un
objeto ``RouteDefinition`` inmutable con la información completa de la ruta.

La clase ``RouteRegistry`` actúa como registro global que valida la unicidad
de handlers por nombre + método HTTP dentro de una misma clase.

Uso típico::

    class MyController(Template):

        @Get("/", response_class=HTMLResponse)
        async def index(self, request: Request) -> HTMLResponse:
            ...

        @Post("/submit")
        async def submit(self, request: Request) -> dict:
            ...
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union, Sequence, Set, Type

from fastapi import Response, params
from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from starlette.routing import BaseRoute


# Sentinel object to distinguish "not provided" from explicit None.
_UNSET: Any = object()


class HTTPMethod(Enum):
    """Enumeración de métodos HTTP soportados por el sistema de rutas."""

    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"
    PUT = "PUT"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass(frozen=True)
class RouteDefinition:
    """Definición inmutable de una ruta HTTP registrada.

    Almacena toda la metadata necesaria para registrar un endpoint
    en FastAPI, incluyendo el método HTTP, path, handler y kwargs adicionales.

    Attributes:
        handler_name: Nombre único del método handler decorado.
        http_method: Método HTTP asociado a esta ruta.
        route_path: Path o lista de paths para la ruta.
        handler: Referencia a la función handler original.
        kwargs: Argumentos adicionales para FastAPI (response_class, etc.).
    """

    handler_name: str
    http_method: HTTPMethod
    route_path: Union[str, List[str]]
    handler: Callable[..., Any]
    kwargs: Dict[str, Any] = field(default_factory=dict)

    @property
    def registry_key(self) -> str:
        """Genera la clave única de registro: '{HTTP_METHOD}:{handler_name}'.

        Returns:
            Clave compuesta por método HTTP y nombre del handler.
        """
        return f"{self.http_method.value}:{self.handler_name}"


class RouteRegistry:
    """Registro que almacena y valida definiciones de rutas por clase.

    Cada clase controladora tiene su propio espacio de nombres aislado.
    Dentro de un mismo espacio, no pueden existir dos handlers con el
    mismo nombre y método HTTP.

    El registro se realiza a nivel de clase cuando el auto-router
    inspecciona los métodos decorados.
    """

    def __init__(self) -> None:
        """Inicializa el registro con un diccionario vacío por clase."""
        self._registry: Dict[str, Dict[str, RouteDefinition]] = {}

    def register(
        self,
        class_name: str,
        definition: RouteDefinition,
    ) -> None:
        """Registra una definición de ruta para una clase específica.

        Args:
            class_name: Nombre completo de la clase controladora.
            definition: Definición de ruta a registrar.

        Raises:
            DuplicateRouteHandlerError: Si ya existe un handler con el
                mismo nombre y método HTTP en la misma clase.
        """
        from core.lib.register.exceptions import DuplicateRouteHandlerError

        if class_name not in self._registry:
            self._registry[class_name] = {}

        class_routes: Dict[str, RouteDefinition] = self._registry[class_name]
        registry_key: str = definition.registry_key

        if registry_key in class_routes:
            existing_definition: RouteDefinition = class_routes[registry_key]
            raise DuplicateRouteHandlerError(
                handler_name=definition.handler_name,
                http_method=definition.http_method.value,
                existing_module=existing_definition.handler.__module__,
                conflicting_module=definition.handler.__module__,
            )

        class_routes[registry_key] = definition

    def get_routes_for_class(
        self,
        class_name: str,
    ) -> List[RouteDefinition]:
        """Obtiene todas las definiciones de ruta registradas para una clase.

        Args:
            class_name: Nombre completo de la clase controladora.

        Returns:
            Lista de definiciones de ruta asociadas a la clase.
            Retorna lista vacía si la clase no tiene rutas registradas.
        """
        class_routes: Dict[str, RouteDefinition] = self._registry.get(class_name, {})
        return list(class_routes.values())

    def clear(self) -> None:
        """Limpia todas las definiciones de ruta registradas.

        Útil para testing y reseteo del estado global.
        """
        self._registry.clear()


# ---------------------------------------------------------------------------
# Instancia global del registro de rutas
# ---------------------------------------------------------------------------
route_registry: RouteRegistry = RouteRegistry()


def route(
    http_method: HTTPMethod,
    route_path: Union[str, List[str]] = "/",
    *,
    response_model: Any = _UNSET,
    status_code: Optional[int] = _UNSET,
    tags: Optional[List[Union[str, Enum]]] = _UNSET,
    dependencies: Optional[Sequence[params.Depends]] = _UNSET,
    summary: Optional[str] = _UNSET,
    description: Optional[str] = _UNSET,
    response_description: str = _UNSET,
    responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = _UNSET,
    deprecated: Optional[bool] = _UNSET,
    operation_id: Optional[str] = _UNSET,
    response_model_include: Optional[Any] = _UNSET,
    response_model_exclude: Optional[Any] = _UNSET,
    response_model_exclude_unset: bool = _UNSET,
    response_model_exclude_defaults: bool = _UNSET,
    response_model_exclude_none: bool = _UNSET,
    include_in_schema: bool = _UNSET,
    response_class: Type[Response] = _UNSET,
    name: Optional[str] = _UNSET,
    callbacks: Optional[List[BaseRoute]] = _UNSET,
    openapi_extra: Optional[Dict[str, Any]] = _UNSET,
    generate_unique_id_function: Callable[[APIRoute], str] = _UNSET,
    **kwargs: Any,
) -> Callable[..., Any]:
    """Decorador base que define una ruta HTTP para un método handler.

    Almacena la metadata de la ruta directamente en el método decorado
    a través de atributos dunder (``__route_definition__``, ``__http_method__``,
    ``__route_path__``, ``__kwargs__``).

    Este decorador NO registra la ruta en el ``RouteRegistry`` global de forma
    inmediata. El registro se realiza cuando el auto-router inspecciona la clase
    y llama a ``route_registry.register()``.

    Args:
        http_method: Método HTTP para la ruta (GET, POST, DELETE, etc.).
        route_path: Path o lista de paths para la ruta. Ejemplo: "/users".
        **kwargs: Argumentos adicionales para FastAPI (response_class, dependencies, etc.).

    Returns:
        Función decoradora que envuelve al handler original.
    """

    # Collect only explicitly provided parameters, skip _UNSET ones
    # so FastAPI's own defaults are preserved.
    _explicit: Dict[str, Any] = {
        "response_model": response_model,
        "status_code": status_code,
        "tags": tags,
        "dependencies": dependencies,
        "summary": summary,
        "description": description,
        "response_description": response_description,
        "responses": responses,
        "deprecated": deprecated,
        "operation_id": operation_id,
        "response_model_include": response_model_include,
        "response_model_exclude": response_model_exclude,
        "response_model_exclude_unset": response_model_exclude_unset,
        "response_model_exclude_defaults": response_model_exclude_defaults,
        "response_model_exclude_none": response_model_exclude_none,
        "include_in_schema": include_in_schema,
        "response_class": response_class,
        "name": name,
        "callbacks": callbacks,
        "openapi_extra": openapi_extra,
        "generate_unique_id_function": generate_unique_id_function,
    }
    all_kwargs: Dict[str, Any] = {
        k: v for k, v in _explicit.items() if v is not _UNSET
    }
    all_kwargs.update(kwargs)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        shield_deps = getattr(func, "__dependencies__", [])
        if shield_deps:
            provided_deps = all_kwargs.get("dependencies")
            if provided_deps is None:
                provided_deps = []
            elif not isinstance(provided_deps, list):
                provided_deps = list(provided_deps)
            all_kwargs["dependencies"] = provided_deps + list(shield_deps)

        route_definition: RouteDefinition = RouteDefinition(
            handler_name=getattr(func, "__name__", "unknown"),
            http_method=http_method,
            route_path=route_path,
            handler=func,
            kwargs=all_kwargs,
        )

        # Almacenar metadata en el método decorado para inspección posterior
        setattr(func, "__route_definition__", route_definition)
        setattr(func, "__http_method__", http_method)
        setattr(func, "__route_path__", route_path)
        setattr(func, "__kwargs__", all_kwargs)

        return func

    return decorator


# ---------------------------------------------------------------------------
# Decoradores shortcut para cada método HTTP
# ---------------------------------------------------------------------------


def Get(
    route_path: Union[str, List[str]] = "/",
    *,
    response_model: Any = _UNSET,
    status_code: Optional[int] = _UNSET,
    tags: Optional[List[Union[str, Enum]]] = _UNSET,
    dependencies: Optional[Sequence[params.Depends]] = _UNSET,
    summary: Optional[str] = _UNSET,
    description: Optional[str] = _UNSET,
    response_description: str = _UNSET,
    responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = _UNSET,
    deprecated: Optional[bool] = _UNSET,
    operation_id: Optional[str] = _UNSET,
    response_model_include: Optional[Any] = _UNSET,
    response_model_exclude: Optional[Any] = _UNSET,
    response_model_exclude_unset: bool = _UNSET,
    response_model_exclude_defaults: bool = _UNSET,
    response_model_exclude_none: bool = _UNSET,
    include_in_schema: bool = _UNSET,
    response_class: Type[Response] = _UNSET,
    name: Optional[str] = _UNSET,
    callbacks: Optional[List[BaseRoute]] = _UNSET,
    openapi_extra: Optional[Dict[str, Any]] = _UNSET,
    generate_unique_id_function: Callable[[APIRoute], str] = _UNSET,
    **kwargs: Any,
) -> Callable[..., Any]:
    """Decorador para rutas HTTP GET."""
    _params = locals()
    _params.pop("route_path")
    _params.pop("kwargs")
    return route(HTTPMethod.GET, route_path, **_params, **kwargs)


def Post(
    route_path: Union[str, List[str]] = "/",
    *,
    response_model: Any = _UNSET,
    status_code: Optional[int] = _UNSET,
    tags: Optional[List[Union[str, Enum]]] = _UNSET,
    dependencies: Optional[Sequence[params.Depends]] = _UNSET,
    summary: Optional[str] = _UNSET,
    description: Optional[str] = _UNSET,
    response_description: str = _UNSET,
    responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = _UNSET,
    deprecated: Optional[bool] = _UNSET,
    operation_id: Optional[str] = _UNSET,
    response_model_include: Optional[Any] = _UNSET,
    response_model_exclude: Optional[Any] = _UNSET,
    response_model_exclude_unset: bool = _UNSET,
    response_model_exclude_defaults: bool = _UNSET,
    response_model_exclude_none: bool = _UNSET,
    include_in_schema: bool = _UNSET,
    response_class: Type[Response] = _UNSET,
    name: Optional[str] = _UNSET,
    callbacks: Optional[List[BaseRoute]] = _UNSET,
    openapi_extra: Optional[Dict[str, Any]] = _UNSET,
    generate_unique_id_function: Callable[[APIRoute], str] = _UNSET,
    **kwargs: Any,
) -> Callable[..., Any]:
    """Decorador para rutas HTTP POST."""
    _params = locals()
    _params.pop("route_path")
    _params.pop("kwargs")
    return route(HTTPMethod.POST, route_path, **_params, **kwargs)


def Delete(
    route_path: Union[str, List[str]] = "/",
    *,
    response_model: Any = _UNSET,
    status_code: Optional[int] = _UNSET,
    tags: Optional[List[Union[str, Enum]]] = _UNSET,
    dependencies: Optional[Sequence[params.Depends]] = _UNSET,
    summary: Optional[str] = _UNSET,
    description: Optional[str] = _UNSET,
    response_description: str = _UNSET,
    responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = _UNSET,
    deprecated: Optional[bool] = _UNSET,
    operation_id: Optional[str] = _UNSET,
    response_model_include: Optional[Any] = _UNSET,
    response_model_exclude: Optional[Any] = _UNSET,
    response_model_exclude_unset: bool = _UNSET,
    response_model_exclude_defaults: bool = _UNSET,
    response_model_exclude_none: bool = _UNSET,
    include_in_schema: bool = _UNSET,
    response_class: Type[Response] = _UNSET,
    name: Optional[str] = _UNSET,
    callbacks: Optional[List[BaseRoute]] = _UNSET,
    openapi_extra: Optional[Dict[str, Any]] = _UNSET,
    generate_unique_id_function: Callable[[APIRoute], str] = _UNSET,
    **kwargs: Any,
) -> Callable[..., Any]:
    """Decorador para rutas HTTP DELETE."""
    _params = locals()
    _params.pop("route_path")
    _params.pop("kwargs")
    return route(HTTPMethod.DELETE, route_path, **_params, **kwargs)


def Put(
    route_path: Union[str, List[str]] = "/",
    *,
    response_model: Any = _UNSET,
    status_code: Optional[int] = _UNSET,
    tags: Optional[List[Union[str, Enum]]] = _UNSET,
    dependencies: Optional[Sequence[params.Depends]] = _UNSET,
    summary: Optional[str] = _UNSET,
    description: Optional[str] = _UNSET,
    response_description: str = _UNSET,
    responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = _UNSET,
    deprecated: Optional[bool] = _UNSET,
    operation_id: Optional[str] = _UNSET,
    response_model_include: Optional[Any] = _UNSET,
    response_model_exclude: Optional[Any] = _UNSET,
    response_model_exclude_unset: bool = _UNSET,
    response_model_exclude_defaults: bool = _UNSET,
    response_model_exclude_none: bool = _UNSET,
    include_in_schema: bool = _UNSET,
    response_class: Type[Response] = _UNSET,
    name: Optional[str] = _UNSET,
    callbacks: Optional[List[BaseRoute]] = _UNSET,
    openapi_extra: Optional[Dict[str, Any]] = _UNSET,
    generate_unique_id_function: Callable[[APIRoute], str] = _UNSET,
    **kwargs: Any,
) -> Callable[..., Any]:
    """Decorador para rutas HTTP PUT."""
    _params = locals()
    _params.pop("route_path")
    _params.pop("kwargs")
    return route(HTTPMethod.PUT, route_path, **_params, **kwargs)


def Patch(
    route_path: Union[str, List[str]] = "/",
    *,
    response_model: Any = _UNSET,
    status_code: Optional[int] = _UNSET,
    tags: Optional[List[Union[str, Enum]]] = _UNSET,
    dependencies: Optional[Sequence[params.Depends]] = _UNSET,
    summary: Optional[str] = _UNSET,
    description: Optional[str] = _UNSET,
    response_description: str = _UNSET,
    responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = _UNSET,
    deprecated: Optional[bool] = _UNSET,
    operation_id: Optional[str] = _UNSET,
    response_model_include: Optional[Any] = _UNSET,
    response_model_exclude: Optional[Any] = _UNSET,
    response_model_exclude_unset: bool = _UNSET,
    response_model_exclude_defaults: bool = _UNSET,
    response_model_exclude_none: bool = _UNSET,
    include_in_schema: bool = _UNSET,
    response_class: Type[Response] = _UNSET,
    name: Optional[str] = _UNSET,
    callbacks: Optional[List[BaseRoute]] = _UNSET,
    openapi_extra: Optional[Dict[str, Any]] = _UNSET,
    generate_unique_id_function: Callable[[APIRoute], str] = _UNSET,
    **kwargs: Any,
) -> Callable[..., Any]:
    """Decorador para rutas HTTP PATCH."""
    _params = locals()
    _params.pop("route_path")
    _params.pop("kwargs")
    return route(HTTPMethod.PATCH, route_path, **_params, **kwargs)


def Head(
    route_path: Union[str, List[str]] = "/",
    *,
    response_model: Any = _UNSET,
    status_code: Optional[int] = _UNSET,
    tags: Optional[List[Union[str, Enum]]] = _UNSET,
    dependencies: Optional[Sequence[params.Depends]] = _UNSET,
    summary: Optional[str] = _UNSET,
    description: Optional[str] = _UNSET,
    response_description: str = _UNSET,
    responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = _UNSET,
    deprecated: Optional[bool] = _UNSET,
    operation_id: Optional[str] = _UNSET,
    response_model_include: Optional[Any] = _UNSET,
    response_model_exclude: Optional[Any] = _UNSET,
    response_model_exclude_unset: bool = _UNSET,
    response_model_exclude_defaults: bool = _UNSET,
    response_model_exclude_none: bool = _UNSET,
    include_in_schema: bool = _UNSET,
    response_class: Type[Response] = _UNSET,
    name: Optional[str] = _UNSET,
    callbacks: Optional[List[BaseRoute]] = _UNSET,
    openapi_extra: Optional[Dict[str, Any]] = _UNSET,
    generate_unique_id_function: Callable[[APIRoute], str] = _UNSET,
    **kwargs: Any,
) -> Callable[..., Any]:
    """Decorador para rutas HTTP HEAD."""
    _params = locals()
    _params.pop("route_path")
    _params.pop("kwargs")
    return route(HTTPMethod.HEAD, route_path, **_params, **kwargs)


def Options(
    route_path: Union[str, List[str]] = "/",
    *,
    response_model: Any = _UNSET,
    status_code: Optional[int] = _UNSET,
    tags: Optional[List[Union[str, Enum]]] = _UNSET,
    dependencies: Optional[Sequence[params.Depends]] = _UNSET,
    summary: Optional[str] = _UNSET,
    description: Optional[str] = _UNSET,
    response_description: str = _UNSET,
    responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = _UNSET,
    deprecated: Optional[bool] = _UNSET,
    operation_id: Optional[str] = _UNSET,
    response_model_include: Optional[Any] = _UNSET,
    response_model_exclude: Optional[Any] = _UNSET,
    response_model_exclude_unset: bool = _UNSET,
    response_model_exclude_defaults: bool = _UNSET,
    response_model_exclude_none: bool = _UNSET,
    include_in_schema: bool = _UNSET,
    response_class: Type[Response] = _UNSET,
    name: Optional[str] = _UNSET,
    callbacks: Optional[List[BaseRoute]] = _UNSET,
    openapi_extra: Optional[Dict[str, Any]] = _UNSET,
    generate_unique_id_function: Callable[[APIRoute], str] = _UNSET,
    **kwargs: Any,
) -> Callable[..., Any]:
    """Decorador para rutas HTTP OPTIONS."""
    _params = locals()
    _params.pop("route_path")
    _params.pop("kwargs")
    return route(HTTPMethod.OPTIONS, route_path, **_params, **kwargs)

