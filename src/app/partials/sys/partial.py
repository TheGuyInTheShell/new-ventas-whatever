from core.lib.decorators import Get, Post, Services
from core.lib.register import Partial, Services
from typing import Annotated

from src.modules.users.services import UsersService
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_async_db
from fastapi import Depends, Form as FastAPIForm
from fastapi.responses import Response
from fasthtml.common import Div, H1, P
from core.security.csrf.csrf import CSRF


@Services(UsersService)
class SysPartials(Partial):
    """Controlador de parciales para el sistema."""

    UsersService: "UsersService"

    @Get("/", response_class=Response)
    async def init_system_with_credentials(
        self,
        username: Annotated[str, FastAPIForm()],
        password: Annotated[str, FastAPIForm()],
        email: Annotated[str, FastAPIForm()],
        full_name: Annotated[str, FastAPIForm()],
    ) -> Response:
        """Retorna el fragmento HTML con el mensaje de bienvenida cuando la creacion del primer usuario es exitosa, si no, retorna un mensaje de error."""

        response = str(
            Div(
                H1("Welcome to the system"),
                P("Please create your first user to continue"),
                cls="success-msg alert alert-success text-white text-sm font-semibold rounded-lg shadow-md p-3 animate-bounce flex items-center justify-center w-full",
            )
        )

        return Response(response)
