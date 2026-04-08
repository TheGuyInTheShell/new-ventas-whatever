from typing import TYPE_CHECKING, Union, Any

if TYPE_CHECKING:
    from fastapi.templating import Jinja2Templates


class Partial:
    """Clase base para controladores de endpoints API.

    Proporciona una base limpia para definir endpoints de API REST.
    No recibe proveedor de templates ni dependencias en el constructor,
    manteniendo los controllers API desacoplados de la capa de presentación.

    Las subclases definen métodos decorados con ``@Get``, ``@Post``, etc.
    que el auto-router descubre y registra automáticamente en FastAPI.

    Attributes:
        templates: Instancia del proveedor de templates inyectado.
            Permite a los partials renderizar fragmentos de HTML.

    Ejemplo::

        class ProductsController(Controller):

            @Get("/")
            async def list_products(self) -> list[dict]:
                return [{"id": 1, "name": "Widget"}]
    """

    templates:  Union["Jinja2Templates", Any]

    def __init__(self, template_provider: any) -> None:
        """Inicializa el controller de partials con el proveedor de templates.

        Args:
            template_provider: Instancia del motor de renderizado de templates.
        """
        self.templates = template_provider