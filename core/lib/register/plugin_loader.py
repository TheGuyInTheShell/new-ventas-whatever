import importlib.util
import inspect
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, List
from core.events import ChannelEvent

from fastapi import FastAPI

from core.lib.register.plugin import Plugin


def _load_plugins(app: FastAPI) -> List[Plugin]:
    """
    Dynamically loads all plugins from the `plugins/` directory.
    To be considered a plugin, the folder must contain a python file
    with the exact same name as the folder (e.g. plugins/my-plugin/my-plugin.py).
    Inside that module, it searches for subclasses of `Plugin`.
    """
    instances: List[Plugin] = []
    base_dir = Path("plugins")

    if not base_dir.exists() or not base_dir.is_dir():
        return instances

    # Iterate over all folders in `plugins/`
    for folder in base_dir.iterdir():
        if folder.is_dir():
            target_file = folder / f"{folder.name}.py"
            if target_file.exists() and target_file.is_file():
                # We create a pseudo-module name that includes the folder name, 
                # supporting folders with hyphens (which aren't valid python identifiers directly).
                # To support relative imports within the plugin, we structure the name gracefully.
                package_name = f"plugins.{folder.name}"
                module_name = f"{package_name}.{folder.name}"
                
                # Mock a package module in sys.modules so relative imports work smoothly
                if package_name not in sys.modules:
                    pkg_spec = importlib.machinery.ModuleSpec(package_name, None, is_package=True)
                    pkg_module = importlib.util.module_from_spec(pkg_spec)
                    pkg_module.__path__ = [str(folder.resolve())]
                    sys.modules[package_name] = pkg_module

                spec = importlib.util.spec_from_file_location(module_name, target_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    # Register module before executing to support recursive/relative imports if any
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)

                    # Inspect the loaded module to find subclasses of Plugin
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        # Ensure obj is a class, a subclass of Plugin, and not Plugin itself
                        if issubclass(obj, Plugin) and obj is not Plugin:
                            # Avoid loading base classes that might be defined in the plugin itself
                            # We only want classes defined in the plugin's module, or we can just load all Plugin subclasses
                            if obj.__module__ == module_name:
                                # Instantiate the plugin and store it
                                plugin_instance = obj(app=app)
                                instances.append(plugin_instance)

    return instances


@asynccontextmanager
async def plugin_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages the lifecycle of plugins for FastAPI application.
    - Loads plugins
    - Dispatches `.init()` on startup
    - Dispatches `.terminate()` on shutdown
    """
    plugins = _load_plugins(app)

    # Execute startup logic
    ChannelEvent().emit_to("app.init").run(app=app)

    # Warm up DB connection pool (async only for now)
    from core.database.drivers.postgres.async_connection import warm_up_async_db
    try:
        await warm_up_async_db()
    except Exception as e:
        print(f"Warning: Database warm-up failed: {e}")

    for plugin in plugins:
        if inspect.iscoroutinefunction(plugin.init):
            await plugin.init()
        else:
            plugin.init()

    # Register injectable dependencies
    from fastapi_injectable import register_app
    await register_app(app)
    
    # Pass control to FastAPI 
    ChannelEvent().emit_to("app.ready").run(app=app)
    
    yield

    # Execute shutdown logic
    ChannelEvent().emit_to("app.shutdown").run(app=app)
    for plugin in plugins:
        if inspect.iscoroutinefunction(plugin.terminate):
            await plugin.terminate()
        else:
            plugin.terminate()
