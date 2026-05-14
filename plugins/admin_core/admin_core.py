from core.lib.register.plugin import Plugin
from fastapi.templating import Jinja2Templates
from core.lib.consts.template import CONTEXT_INJECTABLE
from core.lib.register.auto_router_templates import auto_router_templates
from fastapi import FastAPI

class AdminCore(Plugin):

    def __init__(self, app: FastAPI) -> None:
        self.app = app

    async def init(self):
        
        try:
            admin_templates: Jinja2Templates = Jinja2Templates(directory="plugins/admin_core/web")
            from typing import Any, cast
            globals_dict = cast(dict[str, Any], admin_templates.env.globals)
            globals_dict["_injectable"] = CONTEXT_INJECTABLE
            globals_dict["STATIC_URL"] = "/admin-static"


            # Admin: prefix /admin
            auto_router_templates(
                app=self.app,
                template_provider=admin_templates,
                templates_controllers_path="plugins/admin_core/templates",
                prefix="/admin",
                statics_prefix="/admin-static",
                statics_path="plugins/admin_core/web/out",
            )
            print("✅ Admin Core Plugin initialized")
        except Exception as e:
            print(f"⚠️ Admin Core Plugin failed to initialize: {e}")

    async def terminate(self):
        pass