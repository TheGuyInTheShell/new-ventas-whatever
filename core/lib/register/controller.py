"""
Clase base Controller para controladores de endpoints API.

Proporciona una clase base para definir endpoints de API REST. A diferencia
de ``Template``, esta clase no requiere un proveedor de templates ya que los
endpoints de API retornan datos (JSON, etc.) directamente.

Los métodos del controller se decoran con ``@Get``, ``@Post``, ``@Delete``,
``@Put``, ``@Patch``, ``@Head``, ``@Options`` para definir las rutas HTTP.

El auto-router escanea recursivamente el árbol de directorios buscando
archivos ``controller.py`` que contengan clases heredando de ``Controller``.

Uso típico::

    from core.lib.register import Controller
    from core.lib.decorators import Get, Post, Delete

    class UsersController(Controller):

        @Get("/")
        async def list_users(self) -> list[dict]:
            return [{"id": 1, "name": "John"}]

        @Get("/{user_id}")
        async def get_user(self, user_id: int) -> dict:
            return {"id": user_id, "name": "John"}

        @Post("/")
        async def create_user(self, name: str) -> dict:
            return {"id": 2, "name": name}

        @Delete("/{user_id}")
        async def delete_user(self, user_id: int) -> dict:
            return {"deleted": user_id}
"""

from fastapi import FastAPI


class Controller:
    """Clase base para controladores de endpoints API.

    Proporciona una base limpia para definir endpoints de API REST.
    No recibe proveedor de templates ni dependencias en el constructor,
    manteniendo los controllers API desacoplados de la capa de presentación.

    Las subclases definen métodos decorados con ``@Get``, ``@Post``, etc.
    que el auto-router descubre y registra automáticamente en FastAPI.

    Ejemplo::

        class ProductsController(Controller):

            @Get("/")
            async def list_products(self) -> list[dict]:
                return [{"id": 1, "name": "Widget"}]
    """

    def __init__(self, app: FastAPI, prefix: str) -> None:
        """Inicializa el controller base.

        Las subclases pueden sobreescribir este constructor para inyectar
        servicios u otras dependencias específicas del dominio.
        """
        self.app = app
        self.prefix = prefix
