import os

from importlib import import_module

from fastapi import Depends, FastAPI

from core.config.settings import settings

def auto_router_api(app: FastAPI, base_path: str = "src/api", prefix: str = '/api/v1'):
    for root, dirs, files in os.walk(base_path):
        # Ignore schemas, services and __pycache__ folders
        dirs[:] = [d for d in dirs if d not in ["schemas", "services", "__pycache__", "models"]]
        
        # Normalize paths
        normalized_root = root.replace("\\", "/").rstrip("/").replace("/", ".")
        normalized_base = base_path.replace("\\", "/").rstrip("/").replace("/", ".")
        
        if not normalized_root.startswith(normalized_base):
            continue
            
        module_name = normalized_root[len(normalized_base):].lstrip(".")

        # Handle 'controllers' folder
        if "controllers" in dirs:
            controllers_dir = os.path.join(root, "controllers")
            for f in os.listdir(controllers_dir):
                if f.endswith(".py") and f != "__init__.py":
                    ctrl_name = f[:-3]
                    import_path = f"{normalized_root}.controllers.{ctrl_name}"
                    try:
                        module = import_module(import_path)
                        # Route prefix logic: if filename is 'controller', omit it in the path
                        parts = [module_name, ctrl_name] if module_name else [ctrl_name]
                        if ctrl_name == "controller":
                            parts = [module_name] if module_name else []
                            
                        route_path = "/".join(p for p in parts if p).replace(".", "/")
                        route_prefix = f"{prefix}/{route_path}"
                        
                        app.include_router(
                            module.router,
                            prefix=route_prefix,
                            dependencies=(
                                #[Depends(ROLE_VERIFY())] if module_name != "auth" else []
                            ),
                        )
                        print(f"Importing API module: {import_path}")
                    except Exception as e:
                        print(f"Error importing API module {import_path}: {e}")
            # Don't recurse into 'controllers' folder as we've already imported its files
            dirs.remove("controllers")

        # Handle single 'controller.py' at module root
        if "controller.py" in files:
            try:
                module = import_module(f"{normalized_root}.controller")
                route_prefix = f"{prefix}/{module_name.replace('.', '/')}"
                app.include_router(
                    module.router,
                    prefix=route_prefix,
                    dependencies=(
                        #[Depends(ROLE_VERIFY())] if module_name != "auth" else []
                    ),
                )
                print(f"Importing API module: {module_name}")
            except Exception as e:
                print(f"Error importing API module {module_name}: {e}")

    return app