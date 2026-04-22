import os
import inspect
import sys
import importlib.util
from typing import Callable, Dict, Any, Optional

from .registry import permission_registry
from .types import PermissionDefinition, PermissionMeta


def scan_permissions(
    path: str,
    callback: Callable[[Dict[str, Any]], Any],
    default_context: Optional[str] = None,
) -> None:
    """
    Escanea la ruta especificada buscando clases decoradas con @Shield.register y recolecta
    los permisos declarados con @Shield.need.

    Todos los permisos encontrados heredarán el `default_context` a menos que tengan
    su propio contexto especificado explícitamente en el decorador.

    Nota de Seguridad: Todos los permisos escaneados requieren un Resolver configurado.
    Por defecto, Shield utiliza un `Default401Resolver` que bloqueará el acceso con
    un error 401 si no se asigna un resolver específico durante el escaneo o globalmente.
    """
    normalized_path = path.replace("\\", "/").rstrip("/")

    if not os.path.exists(normalized_path):
        # Si el path no existe, simplemente llamamos al callback con objeto vacio o retornamos
        callback(permission_registry.to_dict())
        return

    # NOTE: We intentionally do NOT clear the registry here.
    # ShieldGroup subclasses self-register via __init_subclass__ at import time.
    # Clearing would wipe those nodes and, on subsequent Shield.scan() calls,
    # they would never be re-added because Python's module cache prevents
    # __init_subclass__ from firing a second time for the same class.
    # Instead, the scanner explicitly calls _register_all() for every
    # ShieldGroup it encounters (see below), which is idempotent thanks to _safe_add.

    for root, dirs, files in os.walk(normalized_path):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                full_path = os.path.join(root, file)
                _inspect_file(full_path, default_context)

    # Una vez que todo el arbol esta construido, se lo pasamos al callback
    callback(permission_registry.to_dict())


def _inspect_file(file_path: str, default_context: Optional[str]) -> None:
    # Convert file path to module name relative to the current working directory.
    # We replace separators with '.' and remove '.py' extension.
    # E.g., 'src/api/health/controller.py' -> 'src.api.health.controller'
    normalized = os.path.normpath(file_path)
    module_name = os.path.splitext(normalized)[0].replace(os.path.sep, ".")

    try:
        module = importlib.import_module(module_name)

        for name, obj in inspect.getmembers(module, inspect.isclass):
            # --- ShieldGroup subclasses (declarative manual trees) ----------
            # We must call _register_all() explicitly here for two reasons:
            # 1. On the first scan the registry was NOT pre-cleared, so we
            #    need to make sure nodes are present (idempotent via _safe_add).
            # 2. On subsequent Shield.scan() calls Python returns the cached
            #    module from sys.modules — __init_subclass__ does NOT fire
            #    again — so without this call the nodes would be missing.
            if (
                hasattr(obj, "__shield_group_marker__")
                and obj.__name__ != "ShieldGroup"
            ):
                obj._register_all()
                continue

            # --- @Shield.register classes (automatic scanner flow) ----------
            # Check if it has the shield register marker
            if hasattr(obj, "__shield_context_marker__"):
                class_context = getattr(obj, "__shield_context__")
                # If the class has no explicit context, it takes the default_context
                final_class_context = (
                    class_context if class_context else default_context
                )

                if not final_class_context:
                    final_class_context = obj.__name__  # Fallback

                # Now inspect its methods for __shield_permissions__
                for method_name, method_obj in inspect.getmembers(obj):
                    if hasattr(method_obj, "__shield_permissions__"):
                        # This is a list of partial PermissionDefinition (dicts or tuples)
                        for p_data in getattr(method_obj, "__shield_permissions__"):
                            context = p_data.get("context")
                            if not context:
                                context = final_class_context

                            raw_meta = p_data["meta"]
                            if isinstance(raw_meta, PermissionMeta):
                                coerced_meta = raw_meta
                            else:
                                coerced_meta = PermissionMeta.from_list(raw_meta)

                            definition = PermissionDefinition(
                                name=p_data["name"],
                                action=p_data["action"],
                                type=p_data["type"],
                                description=p_data["description"],
                                context=context,
                                meta=coerced_meta,
                            )
                            # Registrando en el padre (default_context o el class_context)
                            permission_registry.add(
                                definition,
                                parent_context=(
                                    default_context
                                    if context != default_context
                                    else None
                                ),
                            )

    except Exception as e:
        print(f"[Shield Scanner] Error inspecting {file_path}: {e}")
        pass
