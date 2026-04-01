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
from typing import Any, Callable, Dict, List, Optional, Union


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

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        route_definition: RouteDefinition = RouteDefinition(
            handler_name=func.__name__,
            http_method=http_method,
            route_path=route_path,
            handler=func,
            kwargs=kwargs,
        )

        # Almacenar metadata en el método decorado para inspección posterior
        func.__route_definition__ = route_definition  # type: ignore[attr-defined]
        func.__http_method__ = http_method  # type: ignore[attr-defined]
        func.__route_path__ = route_path  # type: ignore[attr-defined]
        func.__kwargs__ = kwargs  # type: ignore[attr-defined]

        return func

    return decorator


# ---------------------------------------------------------------------------
# Decoradores shortcut para cada método HTTP
# ---------------------------------------------------------------------------


def Get(route_path: Union[str, List[str]] = "/", **kwargs: Any) -> Callable[..., Any]:
    """Decorador para rutas HTTP GET.

    Args:
        route_path: Path o lista de paths para la ruta.
        **kwargs: Argumentos adicionales para FastAPI.

    Returns:
        Función decoradora.
    """
    return route(HTTPMethod.GET, route_path, **kwargs)


def Post(route_path: Union[str, List[str]] = "/", **kwargs: Any) -> Callable[..., Any]:
    """Decorador para rutas HTTP POST.

    Args:
        route_path: Path o lista de paths para la ruta.
        **kwargs: Argumentos adicionales para FastAPI.

    Returns:
        Función decoradora.
    """
    return route(HTTPMethod.POST, route_path, **kwargs)


def Delete(route_path: Union[str, List[str]] = "/", **kwargs: Any) -> Callable[..., Any]:
    """Decorador para rutas HTTP DELETE.

    Args:
        route_path: Path o lista de paths para la ruta.
        **kwargs: Argumentos adicionales para FastAPI.

    Returns:
        Función decoradora.
    """
    return route(HTTPMethod.DELETE, route_path, **kwargs)


def Put(route_path: Union[str, List[str]] = "/", **kwargs: Any) -> Callable[..., Any]:
    """Decorador para rutas HTTP PUT.

    Args:
        route_path: Path o lista de paths para la ruta.
        **kwargs: Argumentos adicionales para FastAPI.

    Returns:
        Función decoradora.
    """
    return route(HTTPMethod.PUT, route_path, **kwargs)


def Patch(route_path: Union[str, List[str]] = "/", **kwargs: Any) -> Callable[..., Any]:
    """Decorador para rutas HTTP PATCH.

    Args:
        route_path: Path o lista de paths para la ruta.
        **kwargs: Argumentos adicionales para FastAPI.

    Returns:
        Función decoradora.
    """
    return route(HTTPMethod.PATCH, route_path, **kwargs)


def Head(route_path: Union[str, List[str]] = "/", **kwargs: Any) -> Callable[..., Any]:
    """Decorador para rutas HTTP HEAD.

    Args:
        route_path: Path o lista de paths para la ruta.
        **kwargs: Argumentos adicionales para FastAPI.

    Returns:
        Función decoradora.
    """
    return route(HTTPMethod.HEAD, route_path, **kwargs)


def Options(route_path: Union[str, List[str]] = "/", **kwargs: Any) -> Callable[..., Any]:
    """Decorador para rutas HTTP OPTIONS.

    Args:
        route_path: Path o lista de paths para la ruta.
        **kwargs: Argumentos adicionales para FastAPI.

    Returns:
        Función decoradora.
    """
    return route(HTTPMethod.OPTIONS, route_path, **kwargs)
