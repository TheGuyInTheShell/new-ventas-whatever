from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from fastapi.templating import Jinja2Templates

class ABCTemplate(ABC):

    def __init__(self, templates: "Jinja2Templates"):
        from fastapi.routing import APIRouter
        self.templates = templates
        self.router = APIRouter(tags=["view"])
        super().__init__()

    @abstractmethod
    def add_endpoints(self):
        pass

    @abstractmethod
    def add_page(self):
        pass 

    def add_all(self):
        self.add_page()
        self.add_endpoints()
        return self