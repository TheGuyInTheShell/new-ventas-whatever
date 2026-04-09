from typing import Callable, Any, TypeVar, Optional, Tuple, Type, overload, Dict
from functools import wraps

from .types import PermissionDefinition, PermissionMeta
from .registry import permission_registry
from .provider import ResolverProvider
from .errors import ShieldPermissionError
from .scanner import scan_permissions

P = TypeVar("P")
R = TypeVar("R")
T = TypeVar("T")

class ShieldArgPlaceholder:
    """Descriptor/Marker para inyeccion de un argumento protegido."""
    def __init__(self, name: str, type_str: str, description: str, default: Any, context: Optional[str], meta: Tuple[Any, Any]):
        self.name = name
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
    
    @staticmethod
    def scan(path: str, callback: Callable[[Dict[str, Any]], Any], context: Optional[str] = None) -> None:
        """Escanea una carpeta recursivamente y expone el arbol de permisos al callback."""
        scan_permissions(path, callback, default_context=context)

    @staticmethod
    def register(cls_or_context: Any = None, *, context: Optional[str] = None) -> Any:
        """
        Decorador de clase.
        Puede usarse como @Shield.register o @Shield.register(context="MyModule")
        """
        def decorator(cls: Type[Any]) -> Type[Any]:
            setattr(cls, "__shield_context_marker__", True)
            ctx = context if context is not None else (cls_or_context if isinstance(cls_or_context, str) else None)
            setattr(cls, "__shield_context__", ctx)
            return cls

        if isinstance(cls_or_context, type):
            # Used as @Shield.register
            return decorator(cls_or_context)
        elif isinstance(cls_or_context, str):
            # Used as @Shield.register("SomeContext")
            context = cls_or_context
            return decorator
            
        return decorator

    @staticmethod
    def need(name: str, description: str, type: str, context: Optional[str] = None, meta: Tuple[Optional[str], Optional[str]] = (None, None)) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """
        Decorador para un endpoint/metodo. Asigna la necesidad de un permiso.
        """
        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            if not hasattr(func, "__shield_permissions__"):
                setattr(func, "__shield_permissions__", [])
            
            p_data = {
                "name": name,
                "description": description,
                "type": type,
                "context": context,
                "meta": PermissionMeta(key=meta[0], value=meta[1])
            }
            getattr(func, "__shield_permissions__").append(p_data)
            
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> R:
                # Ojo: la verificacion en runtime la hara el consumidor con algun middleware o Depends. 
                # Shield como tal aloja las definiciones.
                return func(*args, **kwargs) # type: ignore
            return wrapper # type: ignore
            
        return decorator

    @staticmethod
    def arg(name: str, type: str, description: str, default: T = None, context: Optional[str] = None, meta: Tuple[Optional[str], Optional[str]] = (None, None)) -> Any:
        """
        Asigna el requerimiento de un permiso a un argumento especifico (simulado como marker/descriptor).
        Retorna la instancia del marker.
        """
        # Para integrarse a FastAPI, esto retorna una estructura reconocible 
        # (o podria directamente retornar fastapi.Depends)
        return ShieldArgPlaceholder(
            name=name, type_str=type, description=description, 
            default=default, context=context, meta=meta
        )

    @staticmethod
    def create(name: str, type: str, description: str, context: str, meta: Tuple[Optional[str], Optional[str]] = (None, None), CreationProvider: Optional[Callable[..., Any]] = None) -> None:
        """
        Registro manual imperativo de un permiso.
        """
        definition = PermissionDefinition(
            name=name,
            type=type,
            description=description,
            context=context,
            meta=PermissionMeta(key=meta[0], value=meta[1])
        )
        permission_registry.add(definition)
        if CreationProvider:
            CreationProvider(definition)

    @staticmethod
    def use(name: str, type: str, context: str) -> Callable[[ResolverProvider, Callable[..., Any]], Any]:
        """
        Uso de comprobacion imperativa en codigo.
        Retorna currying function esperando args (Provider, Callback).
        """
        def applier(provider: ResolverProvider, callback: Callable[..., Any]) -> Any:
            # Inject arguments to the provider as requested
            has_permission = provider.resolve(name, type, context)
            if not has_permission:
                raise ShieldPermissionError(name=name, type_str=type, context=context)
            return callback()
            
        return applier
