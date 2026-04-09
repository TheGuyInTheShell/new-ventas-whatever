import functools
import asyncio
from typing import Callable, Any, Optional, List, TypeVar, ParamSpec

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Match
from core.security.csrf.setting import CSRF_SECRET_KEY

P = ParamSpec("P")
R = TypeVar("R")

class CSRFMiddleware:
    """
    Middleware ASGI que valida requests buscando un CSRF Token según la
    configuración del endpoint (__csrf_pattern__).
    """
    def __init__(self, app: Any, provider: Any):
        self.app = app
        self.provider = provider
        
    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Recuperar o generar token actual.
        request = Request(scope, receive=receive)
        csrf_cookie = request.cookies.get("csrf_token")
        
        if csrf_cookie and self.provider.validate_format(csrf_cookie):
            token = csrf_cookie
            is_new = False
        else:
            token = self.provider.generate_token()
            is_new = True
            
        # Inyectar al state
        request.state.csrf_token = token
        
        # Envoltorio para send, de modo que inyectemos la cookie si enviamos headers
        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start" and is_new:
                headers = message.get("headers", [])
                
                # HttpOnly, Path=/, SameSite=Lax (para simplificar entorno genérico)
                # Max-Age: 1 dia (86400)
                cookie_str = f"csrf_token={token}; HttpOnly; Path=/; Max-Age=86400; SameSite=Lax"
                headers.append((b"set-cookie", cookie_str.encode("utf-8")))
                message["headers"] = headers
            await send(message)

        # Buscar el endpoint
        endpoint = None
        for route in request.app.routes:
            match, _ = route.matches(scope)
            if match == Match.FULL:
                endpoint = getattr(route, "endpoint", None)
                break
                                
        # Si no es seguro, debemos revisar
        method = scope.get("method", "").upper()
        if method in ("POST", "PUT", "DELETE", "PATCH") and endpoint is not None:
            config = getattr(endpoint, "__csrf_pattern__", None)
            if config:
                sources = config.get("sources", ["form"])
                
                is_valid = False
                
                # Check header
                if "header" in sources and not is_valid:
                    provided = request.headers.get("x-csrf-token")
                    if provided and provided == token:
                        is_valid = True
                        
                # Check query
                if "query" in sources and not is_valid:
                    provided = request.query_params.get("csrf_token")
                    if provided and provided == token:
                        is_valid = True
                        
                # Check form o json
                if "body" in sources or "form" in sources and not is_valid:
                    # Para leer el body necesitamos almacenar las peticiones de receive
                    # de modo que la ruta original pueda leerlas después.
                    body_bytes = b""
                    more_body = True
                    
                    messages = []
                    while more_body:
                        message = await receive()
                        messages.append(message)
                        more_body = message.get("more_body", False)
                        
                    # Un iterador de mensajes asíncronos para el middleware
                    messages_for_middleware = list(messages)
                    async def middleware_receive() -> dict:
                        if messages_for_middleware:
                            return messages_for_middleware.pop(0)
                        return {"type": "http.request", "body": b"", "more_body": False}
                        
                    # Reconstruir el request base usando un receive exclusivo
                    request = Request(scope, receive=middleware_receive)
                    
                    try:
                        form_data = await request.form()
                        provided = form_data.get("csrf_token") # type: ignore
                        if provided and provided == token:
                            is_valid = True
                    except Exception:
                        pass # si el payload no es form
                    
                    if not is_valid and "body" in sources:
                        try:
                            json_data = await request.json()
                            if isinstance(json_data, dict):
                                provided = json_data.get("csrf_token")
                                if provided and provided == token:
                                    is_valid = True
                        except Exception:
                            pass
                            
                    # Preparamos un iterador fresco para que la aplicación lo consuma normal
                    messages_for_app = list(messages)
                    async def app_receive() -> dict:
                        if messages_for_app:
                            return messages_for_app.pop(0)
                        return {"type": "http.request", "body": b"", "more_body": False}
                        
                    receive = app_receive
                
                if not is_valid:
                    response = JSONResponse(
                        {"detail": "CSRF token missing or incorrect."}, 
                        status_code=403
                    )
                    await response(scope, receive, send_wrapper) # type: ignore
                    return
                    
        await self.app(scope, receive, send_wrapper)

