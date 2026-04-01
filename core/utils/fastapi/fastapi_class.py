from typing import TYPE_CHECKING, List
from fastapi.routing import APIRouter
from enum import Enum
from fastapi_restful.cbv import cbv
if TYPE_CHECKING:
    from fastapi.templating import Jinja2Templates



def fastapi_class(tags: List[str | Enum] = []):
    
    internal_router = APIRouter(tags=tags)

    @cbv(internal_router)
    class ViewFast:
        def __new__(cls):
            cls.router = internal_router
           

        def __init__(self, templates: "Jinja2Templates"):
            self.templates = templates

        
    class WraperView:
        Base = ViewFast
        router = internal_router

    return WraperView
            