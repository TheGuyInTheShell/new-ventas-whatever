import functools
import asyncio
import secrets
import hmac
import hashlib
from typing import Callable, Any, Optional, List, TypeVar, ParamSpec

from fastapi import FastAPI
from core.lib.register.extension import Extension
from .setting import CSRF_SECRET_KEY
from .middleware import CSRFMiddleware

P = ParamSpec("P")
R = TypeVar("R")


class CSRFProvider:
    """Proveedor para generar y validar tokens CSRF."""
    
    def __init__(self, secret: str):
        self.secret = secret.encode("utf-8") if secret else b"default_secret"
        
    def generate_token(self) -> str:
        """Genera un token seguro pseudo-aleatorio."""
        # Using token_hex and signing it or just use token_hex since we save in HttpOnly cookie.
        # Actually with double submit, the token itself just needs to be random 
        # and match between cookie and request.
        salt = secrets.token_hex(16)
        msg = f"{salt}".encode("utf-8")
        signature = hmac.new(self.secret, msg, hashlib.sha256).hexdigest()
        return f"{salt}.{signature}"
        
    def validate_format(self, token: str) -> bool:
        """Valida que un token tenga el formato correcto para no regenerar en cada carga."""
        if not token or "." not in token:
            return False
        parts = token.split(".")
        if len(parts) != 2:
            return False
        salt, signature = parts
        expected = hmac.new(self.secret, salt.encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)


class CSRFExtension(Extension):
    """Extensión para registrar CSRF en la aplicación FastAPI."""
    
    def __init__(self, app: FastAPI):
        self.app = app

    def extends(self):
        # Configuramos el proveedor principal
        provider = CSRFProvider(secret=CSRF_SECRET_KEY or "")
        
        if not hasattr(self.app.state, "csrf"):
            self.app.state.csrf = provider
            
        # Registramos el middleware modificado
        from starlette.middleware import Middleware
        
        # En FastAPI, app.user_middleware se puede mutar o añadir de otra forma.
        # Si se usa add_middleware interactúa con BaseHTTPMiddleware o ASGI
        self.app.add_middleware(CSRFMiddleware, provider=provider)


def CSRF(
    sources: Optional[List[str]] = None
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorador versátil de CSRF (@CSRF):
    1. Agrega metadata (`__csrf_pattern__`) a la ruta para CSRFCheck dinámico.
    2. Actúa como CSRFJinja evaluando la adición del `csrf_token` al contexto global Jinja antes 
       de ejecutar la función para que las plantillas dispongan de `{{ csrf_token }}`.
    """
    if sources is None:
        sources = ["form", "header", "query"]

    def decorator(class_method: Callable[P, R]) -> Callable[P, R]:
        
        # 1. Establecer metadata para CSRFCheck Middleware
        setattr(class_method, "__csrf_pattern__", {"sources": sources})
        
        is_coroutine = asyncio.iscoroutinefunction(class_method)

        # 2. Establecer envoltura para CSRFJinja Injection
        if is_coroutine:
            @functools.wraps(class_method)
            async def async_inner(*args: P.args, **kwargs: P.kwargs) -> Any:
                from starlette.requests import Request
                
                injectable = None
                template_provider = None
                request_obj = None

                # Search request and templates in arguments
                for arg in args:
                    if hasattr(arg, "templates"):
                        template_provider = arg.templates
                
                if "request" in kwargs:
                    request_obj = kwargs["request"]
                else:
                    for arg in args:
                        if isinstance(arg, Request):
                            request_obj = arg
                            break

                try:
                    if template_provider and hasattr(template_provider, "env") and request_obj:
                        injectable = template_provider.env.globals
                        if hasattr(request_obj.state, "csrf_token"):
                            injectable["csrf_token"] = request_obj.state.csrf_token
                            
                    import typing
                    _async_callable = typing.cast(typing.Callable[..., typing.Awaitable[typing.Any]], class_method)
                    return await _async_callable(*args, **kwargs)
                finally:
                    if injectable and "csrf_token" in injectable:
                        del injectable["csrf_token"]
                        
            return async_inner  # type: ignore

        else:
            @functools.wraps(class_method)
            def sync_inner(*args: P.args, **kwargs: P.kwargs) -> Any:
                from starlette.requests import Request

                injectable = None
                template_provider = None
                request_obj = None

                for arg in args:
                    if hasattr(arg, "templates"):
                        template_provider = arg.templates
                
                if "request" in kwargs:
                    request_obj = kwargs["request"]
                else:
                    for arg in args:
                        if isinstance(arg, Request):
                            request_obj = arg
                            break

                try:
                    if template_provider and hasattr(template_provider, "env") and request_obj:
                        injectable = template_provider.env.globals
                        if hasattr(request_obj.state, "csrf_token"):
                            injectable["csrf_token"] = request_obj.state.csrf_token
                            
                    return class_method(*args, **kwargs)
                finally:
                    if injectable and "csrf_token" in injectable:
                        del injectable["csrf_token"]

            return sync_inner  # type: ignore

    return decorator

