import os

from importlib import import_module

from fastapi import Depends, FastAPI

from fastapi.templating import Jinja2Templates

from fastapi.routing import APIRouter

from core.config.settings import settings

def auto_router_templates(app: FastAPI, templates: Jinja2Templates, templates_controllers_path: str = 'src/admin/templates', prefix: str = '/admin'):

    module_names = [f for f in os.listdir(templates_controllers_path)]

    for module_name in module_names:

        try:

            if module_name.find(".py") != -1 or module_name.find("pycache") != -1:
                continue

            module = import_module(f"src.admin.templates.{module_name}.controller")

            print(f"Importing ADMIN templates {module_name}")

            module.Controller(templates)
            router: APIRouter = module.fc.router 

            app.include_router(
                router,
                prefix=f"{prefix}/{module_name}",
                tags=[f"view - {module_name}"],
            )

        except ValueError as e:

            print(f"Error importing module {module_name}: {e}")
            raise

    return app
