import os
import inspect
import sys
import importlib.util
from typing import Callable, Dict, Any, Optional

from .registry import permission_registry
from .types import PermissionDefinition

def scan_permissions(path: str, callback: Callable[[Dict[str, Any]], Any], default_context: Optional[str] = None) -> None:
    """
    Escanea la ruta especificada buscando clases decoradas con @Shield.register y recolecta
    los permisos declarados con @Shield.need.

    Todos los permisos encontrados heredarán el `default_context` a menos que tengan 
    su propio contexto especificado explícitamente en el decorador.
    """
    normalized_path = path.replace("\\", "/").rstrip("/")
    
    if not os.path.exists(normalized_path):
        # Si el path no existe, simplemente llamamos al callback con objeto vacio o retornamos
        callback(permission_registry.to_dict())
        return

    # Limpiamos el registry temporalmente para evitar estados sucios entre scans
    permission_registry.clear()

    for root, dirs, files in os.walk(normalized_path):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                full_path = os.path.join(root, file)
                _inspect_file(full_path, default_context)

    # Una vez que todo el arbol esta construido, se lo pasamos al callback
    callback(permission_registry.to_dict())


def _inspect_file(file_path: str, default_context: Optional[str]) -> None:
    # Convert file path to module name relative to the current working directory or similar.
    # To keep things simple and safe, we'll try to load it via importlib dynamically without adding it to sys.modules permanently if possible,
    # but since auto_router does it by adding to sys.path, we'll use a robust approach
    module_name = "shield_scan_" + os.path.splitext(os.path.basename(file_path))[0]
    
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Check if it has the shield register marker
                if hasattr(obj, "__shield_context_marker__"):
                    class_context = getattr(obj, "__shield_context__")
                    # If the class has no explicit context, it takes the default_context
                    final_class_context = class_context if class_context else default_context
                    
                    if not final_class_context:
                        final_class_context = obj.__name__ # Fallback
                        
                    # Now inspect its methods for __shield_permissions__
                    for method_name, method_obj in inspect.getmembers(obj):
                        if hasattr(method_obj, "__shield_permissions__"):
                            # This is a list of partial PermissionDefinition (dicts or tuples)
                            for p_data in getattr(method_obj, "__shield_permissions__"):
                                context = p_data.get("context")
                                if not context:
                                    context = final_class_context
                                    
                                definition = PermissionDefinition(
                                    name=p_data["name"],
                                    type=p_data["type"],
                                    description=p_data["description"],
                                    context=context,
                                    meta=p_data["meta"]
                                )
                                # Registrando en el padre (default_context o el class_context)
                                permission_registry.add(definition, parent_context=default_context if context != default_context else None)
                                
    except Exception as e:
        # En caso de error de importacion (dependencias, sintaxis, etc)
        # en modo silencioso pasamos, ya que es un scanner
        pass
