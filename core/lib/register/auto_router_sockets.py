import inspect
import os
import warnings
from importlib import import_module
from typing import Any, List, Type

from fastapi import FastAPI
from socketio import AsyncServer

from core.lib.decorators.ws import init_sio_decorator
from core.lib.register.websocket import WebSocket

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

_SOCKET_MODULE_NAME: str = "events"
_SOCKET_FILE_NAME: str = f"{_SOCKET_MODULE_NAME}.py"


from core.lib.register.exceptions import (
    SocketControllerMissingError,
    SocketFileNotFoundWarning,
)


def _normalize_path_to_module(filesystem_path: str) -> str:
    normalized: str = filesystem_path.replace("\\", "/").rstrip("/")
    return normalized.replace("/", ".")


def _find_socket_classes(module: Any) -> List[Type[WebSocket]]:
    socket_classes: List[Type[WebSocket]] = []

    for _name, obj in inspect.getmembers(module, predicate=inspect.isclass):
        is_socket_subclass: bool = (
            issubclass(obj, WebSocket) and obj is not WebSocket
        )

        if is_socket_subclass:
            socket_classes.append(obj)

    return socket_classes


def auto_router_sockets(
    app: FastAPI,
    sockets_path: str,
    async_mode="asgi",
    cors_allowed_origins=[],
    path="/sio",
    logger=True,
    engineio_logger=True,
    allow_upgrades=True,
) -> FastAPI:
    """Auto-registra manejadores de websockets.

    Escanea recursivamente el directorio en busca de archivos `events.py` que
    contengan clases que hereden de `WebSocket`. 
    Configura el namespace usando el nombre de la carpeta e inicializa el decorador `Sio`.
    """

    sio = AsyncServer(
        async_mode=async_mode,
        cors_allowed_origins=cors_allowed_origins,
        path=path,
        logger=logger,
        engineio_logger=engineio_logger,
        allow_upgrades=allow_upgrades,
    )


    normalized_base_path: str = sockets_path.replace("\\", "/").rstrip("/")

    for current_root, subdirectories, files in os.walk(normalized_base_path):
        subdirectories[:] = [
            directory_name
            for directory_name in subdirectories
            if directory_name not in _IGNORED_DIRECTORIES
        ]

        normalized_root: str = current_root.replace("\\", "/").rstrip("/")

        if _SOCKET_FILE_NAME not in files:
            is_root_directory: bool = normalized_root == normalized_base_path
            if not is_root_directory:
                warnings.warn(
                    SocketFileNotFoundWarning(directory_path=normalized_root),
                    stacklevel=2,
                )
            continue

        folder_name = os.path.basename(normalized_root)
        module_import_path: str = (
            f"{_normalize_path_to_module(normalized_root)}.{_SOCKET_MODULE_NAME}"
        )

        namespace = f"/{folder_name}"

        # Initialize Sio decorator *before* importing the module so that @Sio.on 
        # dynamically picks up the right namespace and sio instance.
        init_sio_decorator(sio=sio, namespace=namespace)

        imported_module: Any = import_module(module_import_path)

        socket_classes: List[Type[WebSocket]] = _find_socket_classes(
            imported_module
        )

        if not socket_classes:
            socket_file_full_path: str = os.path.join(
                normalized_root, _SOCKET_FILE_NAME
            )
            raise SocketControllerMissingError(
                socket_file_path=socket_file_full_path,
                module_path=module_import_path,
            )

        for socket_class in socket_classes:
            # send the sio server instance in the param __init__ WebSocket
            # the namespace need be the name of the folder
            socket_instance = socket_class(sio=sio, module_name=folder_name)

            print(
                f"[auto_router_sockets] Registered: "
                f"class='{socket_class.__name__}' "
                f"namespace='{namespace}' "
                f"module='{module_import_path}'"
            )

    # Mount the SocketIO ASGI app onto FastAPI
    from socketio import ASGIApp
    sio_app = ASGIApp(socketio_server=sio)
    
    # We must mount it at the root of the path provided so FastAPI handles it
    app.mount(path, sio_app)

    return app
