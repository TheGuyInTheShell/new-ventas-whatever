from typing import Callable, Any, TypeVar, Optional, Tuple, Type, overload, Dict, cast, Coroutine, ParamSpec
from functools import wraps
import inspect

from fastapi import Request, Depends, HTTPException

from .types import PermissionDefinition, PermissionMeta
from .registry import permission_registry
from .provider import ResolverProvider, BasicResolverProvider
from .errors import ShieldPermissionError
from .scanner import scan_permissions

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")

class ShieldArgPlaceholder:
    """Descriptor/Marker para inyeccion de un argumento protegido."""
    def __init__(self, name: str, action: str, type_str: str, description: str, default: Any, context: Optional[str], meta: Tuple[Any, Any]):
        self.name = name
        self.action = action
        self.type = type_str
        self.description = description
        self.default = default
        self.context = context
        self.meta = meta
        self.__shield_arg__ = True # marker for the inner logic to detect

    # When used as default value in FastAPI, if somebody accesses it it evaluates, 
    # but FastAPI Depends overrides this behaviour. For the sake of this prompt, 
    # we simulate the structure to be discoverable or compatible.
    # Note: Shield.arg in real FastAPI would likely return a `Depends()` that resolves the permission.

class Shield:
    """Fachada estatica para el framework Shield."""
    
    _global_resolver: Optional[ResolverProvider] = None
    
    @classmethod
    def scan(cls, path: str, callback: Callable[[Dict[str, Any]], Any], context: Optional[str] = None, resolver: Optional[ResolverProvider] = None) -> None:
        """Escanea una carpeta recursivamente y expone el arbol de permisos al callback."""
        if resolver:
            cls._global_resolver = resolver
        scan_permissions(path, callback, default_context=context)

    @staticmethod
    def register(cls_or_context: Optional[Any] = None, *, context: Optional[str] = None) -> Any:
        """
        Decorador de clase.
        Puede usarse como @Shield.register o @Shield.register(context="MyModule")
        """
        def decorator(cls: Type[Any]) -> Type[Any]:
            setattr(cls, "__shield_context_marker__", True)
            ctx = context if context is not None else (cls_or_context.__name__ if inspect.isclass(cls_or_context) else None)
            setattr(cls, "__shield_context__", ctx)
            return cls

        if inspect.isclass(cls_or_context) or isinstance(cls_or_context, type):
            # Used as @Shield.register sin parenthesis
            return decorator(cls_or_context)
            
        return decorator

    @staticmethod
    def need(name: str, action: str, type: str, context: Optional[str] = None, description: str = "", resolver: Optional[ResolverProvider] = None, meta: Tuple[Optional[str], Optional[str]] = (None, None)) -> Callable[[Callable[P, R]], Callable[P, R]]:
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
                "meta": PermissionMeta(key=meta[0], value=meta[1])
            }
            getattr(func, "__shield_permissions__").append(p_data)
            
            if not hasattr(func, "__dependencies__"):
                setattr(func, "__dependencies__", [])
                
            async def shield_guard(request: Request) -> None:
                active_resolver = resolver or Shield._global_resolver
                if active_resolver is None:
                    return
                
                # Determine context: fallback to class or global
                actual_context = context
                if actual_context is None:
                    qualname_parts = func.__qualname__.split(".")
                    if len(qualname_parts) > 1:
                        actual_context = qualname_parts[-2]
                    else:
                        actual_context = "Global"
                
                is_async = inspect.iscoroutinefunction(active_resolver.resolve)
                if is_async:
                    res = await cast(Coroutine[Any, Any, bool], active_resolver.resolve(name=name, type_str=type, action=action, context=actual_context, request=request))
                else:
                    res = cast(bool, active_resolver.resolve(name=name, type_str=type, action=action, context=actual_context, request=request))
                
                if not res:
                    raise HTTPException(status_code=403, detail=f"No tienes el permiso requerido: {name} (acción: {action})")

            getattr(func, "__dependencies__").append(Depends(shield_guard))
            
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> R:
                return func(*args, **kwargs) # type: ignore
            return wrapper # type: ignore
            
        return decorator

    @staticmethod
    def basic(resolver: BasicResolverProvider) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """
        Decorador para endpoints que solo requieren validación a nivel petición (ej. API keys).
        """
        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            if not hasattr(func, "__dependencies__"):
                setattr(func, "__dependencies__", [])
                
            async def basic_guard(request: Request) -> None:
                is_async = inspect.iscoroutinefunction(resolver.resolve)
                if is_async:
                    res = await cast(Coroutine[Any, Any, bool], resolver.resolve(request))
                else:
                    res = cast(bool, resolver.resolve(request))
                    
                if not res:
                    raise HTTPException(status_code=401, detail="Acceso denegado (Invalid/Missing Credentials)")

            getattr(func, "__dependencies__").append(Depends(basic_guard))
            
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> R:
                return func(*args, **kwargs) # type: ignore
            return wrapper # type: ignore
            
        return decorator

    @staticmethod
    def arg(name: str, action: str, type: str, description: str, default: T, context: Optional[str] = None, meta: Tuple[Optional[str], Optional[str]] = (None, None)) -> Any:
        """
        Asigna el requerimiento de un permiso a un argumento especifico (simulado como marker/descriptor).
        Retorna la instancia del marker.
        """
        # Para integrarse a FastAPI, esto retorna una estructura reconocible 
        # (o podria directamente retornar fastapi.Depends)
        return ShieldArgPlaceholder(
            name=name, action=action, type_str=type, description=description, 
            default=default, context=context, meta=meta
        )

    @staticmethod
    def create(name: str, action: str, type: str, description: str, context: str, meta: Tuple[Optional[str], Optional[str]] = (None, None), CreationProvider: Optional[Callable[..., Any]] = None) -> None:
        """
        Registro manual imperativo de un permiso.
        """
        definition = PermissionDefinition(
            name=name,
            action=action,
            type=type,
            description=description,
            context=context,
            meta=PermissionMeta(key=meta[0], value=meta[1])
        )
        permission_registry.add(definition)
        if CreationProvider:
            CreationProvider(definition)

    @staticmethod
    def use(name: str, action: str, type: str, context: str) -> Callable[[ResolverProvider, Callable[..., Any]], Any]:
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
