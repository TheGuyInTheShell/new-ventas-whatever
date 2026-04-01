from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from fastapi.templating import Jinja2Templates

class Template:
    def __init__(self, templates: "Jinja2Templates"):
        self.templates = templates
