import os

from importlib import import_module

from fastapi.routing import APIRouter

def import_webhooks_in(app: APIRouter, base_path: str = "src/webhooks/in", prefix: str = ""):
    for root, dirs, files in os.walk(base_path):
        # Skip folders named schemas or services
        dirs[:] = [d for d in dirs if d not in ["schemas", "services", "__pycache__"]]
        
        normalized_root = root.replace("\\", "/").rstrip("/").replace("/", ".")
        normalized_base = base_path.replace("\\", "/").rstrip("/").replace("/", ".")
        
        if not normalized_root.startswith(normalized_base):
            continue
            
        module_name = normalized_root[len(normalized_base):].lstrip(".")

        if "controllers" in dirs:
            controllers_dir = os.path.join(root, "controllers")
            for f in os.listdir(controllers_dir):
                if f.endswith(".py") and f != "__init__.py":
                    ctrl_name = f[:-3]
                    import_path = f"{normalized_root}.controllers.{ctrl_name}"
                    try:
                        module = import_module(import_path)
                        parts = [module_name, ctrl_name] if module_name else [ctrl_name]
                        if ctrl_name == "controller":
                            parts = [module_name] if module_name else []
                        route_path = "/".join(p for p in parts if p).replace(".", "/")
                        route_prefix = f"{prefix}/{route_path}"
                        
                        app.include_router(
                            module.router,
                            prefix=route_prefix,
                            dependencies=[], # No authentication for webhooks
                        )
                        print(f"Importing Webhook module: {import_path}")
                    except Exception as e:
                        print(f"Error importing Webhook module {import_path}: {e}")
            dirs.remove("controllers")

        if "controller.py" in files:
            try:
                module = import_module(f"{normalized_root}.controller")
                route_prefix = f"{prefix}/{module_name.replace('.', '/')}"
                app.include_router(
                    module.router,
                    prefix=route_prefix,
                    dependencies=[], # No authentication for webhooks
                )
                print(f"Importing Webhook module: {module_name}")
            except Exception as e:
                print(f"Error importing Webhook module {module_name}: {e}")

    return [{"routes": app.routes.copy(), "type": "Webhook"}]


def import_webhooks_out(base_path: str = "src/webhooks/out"):
    for root, dirs, files in os.walk(base_path):
        # Skip folders named schemas or services
        dirs[:] = [d for d in dirs if d not in ["schemas", "services", "__pycache__"]]
        
        if "subscriber.py" in files:
            # Use relative path from current working directory to calculate module path
            rel_path = os.path.relpath(root, os.getcwd())
            normalized_root = rel_path.replace("\\", "/").replace("/", ".")
            module_path = f"{normalized_root}.subscriber"
            try:
                import_module(module_path)
                print(f"Loaded webhook subscriber: {module_path}")
            except Exception as e:
                print(f"Error loading webhook subscriber {module_path}: {e}")