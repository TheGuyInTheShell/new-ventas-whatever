import importlib.util
import importlib.machinery
import inspect
import sys
from pathlib import Path
from typing import List

from fastapi import FastAPI

from core.lib.register.extension import Extension


def load_extensions(app: FastAPI) -> List[Extension]:
    """
    Dynamically loads all extensions from the `extension/` directory.
    To be considered an extension, the folder must contain a python file
    with the exact same name as the folder (e.g. extension/my-extension/my-extension.py).
    Inside that module, it searches for subclasses of `Extension`.
    They are executed immediately in the initialization phase.
    """
    instances: List[Extension] = []
    base_dir = Path("extension")

    if not base_dir.exists() or not base_dir.is_dir():
        return instances

    # Iterate over all folders in `extension/`
    for folder in base_dir.iterdir():
        if folder.is_dir():
            target_file = folder / f"{folder.name}.py"
            if target_file.exists() and target_file.is_file():
                # We create a pseudo-module name that includes the folder name,
                # supporting folders with hyphens (which aren't valid python identifiers directly).
                # To support relative imports within the extension, we structure the name gracefully.
                package_name = f"extension.{folder.name}"
                module_name = f"{package_name}.{folder.name}"

                # Mock a package module in sys.modules so relative imports work smoothly
                if package_name not in sys.modules:
                    pkg_spec = importlib.machinery.ModuleSpec(
                        package_name, None, is_package=True
                    )
                    pkg_module = importlib.util.module_from_spec(pkg_spec)
                    pkg_module.__path__ = [str(folder.resolve())]
                    sys.modules[package_name] = pkg_module

                spec = importlib.util.spec_from_file_location(module_name, target_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    # Register module before executing to support recursive/relative imports if any
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)

                    # Inspect the loaded module to find subclasses of Extension
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        # Ensure obj is a class, a subclass of Extension, and not Extension itself
                        if issubclass(obj, Extension) and obj is not Extension:
                            # We only want classes defined in the extension's module
                            if obj.__module__ == module_name:
                                # Instantiate the extension and trigger .extends() immediately
                                extension_instance = obj(app=app)
                                extension_instance.extends()
                                instances.append(extension_instance)

    from core.security.csrf.csrf import CSRFExtension
    from core.security.guards import FastAPI_Guard

    CSRFExtension(app).extends()
    FastAPI_Guard(app).extends()

    return instances
