from typing import (
    Callable,
    Any,
    TypeVar,
    Optional,
    Tuple,
    Type,
    List,
    Dict,
    cast,
    Coroutine,
    ParamSpec,
)
from functools import wraps
import inspect

from fastapi import Request, Depends, HTTPException

from .types import PermissionDefinition, PermissionMeta, CanNode
from .registry import permission_registry
from .provider import ResolverProvider, BasicResolverProvider, Default401Resolver
from .errors import ShieldPermissionError
from .scanner import scan_permissions

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")


class ShieldArgPlaceholder:
    """Descriptor/Marker para inyeccion de un argumento protegido."""

    def __init__(
        self,
        name: str,
        action: str,
        type_str: str,
        description: str,
        default: Any,
        context: Optional[str],
        meta: Tuple[Any, Any],
    ):
        self.name = name
        self.action = action
        self.type = type_str
        self.description = description
        self.default = default
        self.context = context
        self.meta = meta
        self.__shield_arg__ = True  # marker for the inner logic to detect

    # When used as default value in FastAPI, if somebody accesses it it evaluates,
    # but FastAPI Depends overrides this behaviour. For the sake of this prompt,
    # we simulate the structure to be discoverable or compatible.
    # Note: Shield.arg in real FastAPI would likely return a `Depends()` that resolves the permission.


class Shield:
    """Fachada estatica para el framework Shield."""

    _resolvers: Dict[str, ResolverProvider] = {}
    _path_resolvers: Dict[str, ResolverProvider] = {}
    _global_resolver: ResolverProvider = Default401Resolver()

    @classmethod
    def scan(
        cls,
        path: str,
        callback: Callable[[Dict[str, Any]], Any],
        context: Optional[str] = None,
        resolver: Optional[ResolverProvider] = None,
    ) -> None:
        """Escanea una carpeta recursivamente y expone el arbol de permisos al callback."""
        if resolver:
            # Map by path for runtime module-based resolution
            cls._path_resolvers[path] = resolver
            if context:
                cls._resolvers[context] = resolver
            else:
                cls._global_resolver = resolver
        scan_permissions(path, callback, default_context=context)

    @staticmethod
    def register(
        cls_or_context: Optional[Any] = None, *, context: Optional[str] = None
    ) -> Any:
        """
        Decorador de clase.
        Puede usarse como @Shield.register o @Shield.register(context="MyModule")
        """

        def decorator(cls: Type[Any]) -> Type[Any]:
            setattr(cls, "__shield_context_marker__", True)
            ctx = context if context is not None else (cls.__name__)
            setattr(cls, "__shield_context__", ctx)

            # Inject class context into all @Shield.need guards that were
            # registered without an explicit context (holder[0] is None).
            # This avoids the fragile runtime globals lookup in shield_guard.
            for _, method_obj in inspect.getmembers(cls, predicate=callable):
                if hasattr(method_obj, "__shield_context_holders__"):
                    for holder in method_obj.__shield_context_holders__:
                        if holder[0] is None:
                            holder[0] = ctx

            return cls

        if inspect.isclass(cls_or_context) or isinstance(cls_or_context, type):
            # Used as @Shield.register sin parenthesis
            return decorator(cls_or_context)

        return decorator

    @staticmethod
    def need(
        name: str,
        action: str,
        type: str,
        context: Optional[str] = None,
        description: str = "",
        resolver: Optional[ResolverProvider] = None,
        meta: List[Tuple[Optional[str], Optional[str]]] = [(None, None)],
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """
        Decorador para un endpoint/metodo. Asigna la necesidad de un permiso.
        """

        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            if not hasattr(func, "__shield_permissions__"):
                setattr(func, "__shield_permissions__", [])

            p_data = {
                "name": name,
                "action": action,
                "description": description,
                "type": type,
                "context": context,
                "meta": meta,
            }
            getattr(func, "__shield_permissions__").append(p_data)

            if not hasattr(func, "__dependencies__"):
                setattr(func, "__dependencies__", [])

            # Mutable holder so @Shield.register can inject the class context
            # without relying on a fragile runtime globals lookup.
            context_holder: List[Optional[str]] = [context]
            if not hasattr(func, "__shield_context_holders__"):
                setattr(func, "__shield_context_holders__", [])
            getattr(func, "__shield_context_holders__").append(context_holder)

            async def shield_guard(request: Request) -> None:
                # 1. Primary: context injected by @Shield.register at decoration time
                actual_context = context_holder[0]

                # 2. Fallback: runtime globals lookup (in case @Shield.register was not used)
                if actual_context is None:
                    try:
                        cls_name = func.__qualname__.split(".")[0]
                        if cls_name in func.__globals__:
                            cls_obj = func.__globals__[cls_name]
                            if hasattr(cls_obj, "__shield_context__"):
                                actual_context = getattr(cls_obj, "__shield_context__")
                    except Exception:
                        pass

                # 3. Last resort
                if actual_context is None:
                    actual_context = "Global"

                # 2. Pick explicit or context-mapped resolver
                active_resolver = resolver
                if not active_resolver:
                    active_resolver = Shield._resolvers.get(actual_context)

                # 3. Path-based resolver (from scan origin)
                if not active_resolver:
                    module_name = func.__module__
                    for scan_path, scan_resolver in Shield._path_resolvers.items():
                        # normalize path to module prefix: "src/api" -> "src.api"
                        prefix = scan_path.replace("\\", ".").replace("/", ".")
                        if module_name.startswith(prefix):
                            active_resolver = scan_resolver
                            break

                if active_resolver is None:
                    # Closing the vector of attack: if no resolver is found,
                    # we must jump to the Default401Resolver manually if it wasn't picked up.
                    active_resolver = Shield._global_resolver

                is_async = inspect.iscoroutinefunction(active_resolver.resolve)
                if is_async:
                    res = await cast(
                        Coroutine[Any, Any, bool],
                        active_resolver.resolve(
                            name=name,
                            type_str=type,
                            action=action,
                            context=actual_context,
                            request=request,
                        ),
                    )
                else:
                    res = cast(
                        bool,
                        active_resolver.resolve(
                            name=name,
                            type_str=type,
                            action=action,
                            context=actual_context,
                            request=request,
                        ),
                    )

                if not res:
                    raise HTTPException(
                        status_code=403,
                        detail=f"No tienes el permiso requerido: {name} (acción: {action})",
                    )

            getattr(func, "__dependencies__").append(Depends(shield_guard))

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> R:
                return func(*args, **kwargs)  # type: ignore

            return wrapper  # type: ignore

        return decorator

    @staticmethod
    def basic(
        resolver: BasicResolverProvider,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """
        Decorador para endpoints que solo requieren validación a nivel petición (ej. API keys).
        """

        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            if not hasattr(func, "__dependencies__"):
                setattr(func, "__dependencies__", [])

            async def basic_guard(request: Request) -> None:
                is_async = inspect.iscoroutinefunction(resolver.resolve)
                if is_async:
                    res = await cast(
                        Coroutine[Any, Any, bool], resolver.resolve(request)
                    )
                else:
                    res = cast(bool, resolver.resolve(request))

                if not res:
                    raise HTTPException(
                        status_code=401,
                        detail="Acceso denegado (Invalid/Missing Credentials)",
                    )

            getattr(func, "__dependencies__").append(Depends(basic_guard))

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> R:
                return func(*args, **kwargs)  # type: ignore

            return wrapper  # type: ignore

        return decorator

    @staticmethod
    def arg(
        name: str,
        action: str,
        type: str,
        description: str,
        default: T,
        context: Optional[str] = None,
        meta: Tuple[Optional[str], Optional[str]] = (None, None),
    ) -> Any:
        """
        Asigna el requerimiento de un permiso a un argumento especifico (simulado como marker/descriptor).
        Retorna la instancia del marker.
        """
        # Para integrarse a FastAPI, esto retorna una estructura reconocible
        # (o podria directamente retornar fastapi.Depends)
        return ShieldArgPlaceholder(
            name=name,
            action=action,
            type_str=type,
            description=description,
            default=default,
            context=context,
            meta=meta,
        )

    @staticmethod
    def create(
        name: str,
        action: str,
        type: str,
        description: str,
        context: str,
        meta: List[Tuple[Optional[str], Optional[str]]] = [(None, None)],
        CreationProvider: Optional[Callable[..., Any]] = None,
    ) -> None:
        """
        Registro manual imperativo de un permiso.
        """
        definition = PermissionDefinition(
            name=name,
            action=action,
            type=type,
            description=description,
            context=context,
            meta=PermissionMeta.from_list(meta),
        )
        permission_registry.add(definition)
        if CreationProvider:
            CreationProvider(definition)

    @staticmethod
    def use(
        name: str, action: str, type: str, context: str
    ) -> Callable[[ResolverProvider, Callable[..., Any]], Any]:
        """
        Uso de comprobacion imperativa en codigo.
        Retorna currying function esperando args (Provider, Callback).
        """

        def applier(provider: ResolverProvider, callback: Callable[..., Any]) -> Any:
            # Inject arguments to the provider as requested
            has_permission = provider.resolve(name, type, action, context)
            if not has_permission:
                raise ShieldPermissionError(name=name, type_str=type, context=context)
            return callback()

        return applier

    @staticmethod
    def can(
        name: str,
        action: str,
        type_str: str,
        description: str,
        meta: Optional[List[Tuple[Optional[str], Optional[str]]]] = None,
    ) -> CanNode:
        """
        Crea un descriptor de permiso declarativo (``CanNode``) para usar
        dentro de una clase ``ShieldGroup`` o ``ChildrenClass``.

        El contexto **no** se pasa aquí; lo hereda del ``ShieldGroup`` padre
        en el momento del registro.

        Parámetros
        ----------
        name:
            Identificador único del permiso (ej. ``"chinese_restaurant.menu"``).
        action:
            Operación protegida (ej. ``"read"``, ``"write"``, ``"execute"``).
        type_str:
            Categoría funcional del permiso (ej. ``"ui"``, ``"api"``).
        description:
            Descripción legible del permiso (requerida).
        meta:
            Lista de pares ``[(key, value), ...]`` para metadata extendida.

        Ejemplo::

            Shield.can(
                "chinese_restaurant", "read", "ui",
                description="Acceso al módulo restaurante",
                meta=[("icon", "mdi-food-fork-drink")],
            ).children(ChineseRestaurantChildren)
        """
        return CanNode(
            name=name,
            action=action,
            type_str=type_str,
            description=description,
            meta=meta,
        )
