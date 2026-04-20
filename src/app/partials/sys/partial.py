from core.lib.decorators import Get, Post, Services
from core.lib.register import Partial
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

    @Post("/", response_class=Response)
    async def init_system_with_credentials(
        self,
        username: Annotated[str, FastAPIForm()],
        password: Annotated[str, FastAPIForm()],
        email: Annotated[str, FastAPIForm()],
        full_name: Annotated[str, FastAPIForm()],
    ) -> Response:
        """
        Intersepta el formulario de creación del primer usuario y procede con la inicialización.
        """
        try:
            # Crear el usuario owner usando el servicio inyectado
            await self.UsersService.create_owner(
                username=username, password=password, email=email, full_name=full_name
            )

            # Fragmento de éxito con estética premium
            response = str(
                Div(
                    H1("Owner Created Successfully", cls="text-2xl font-bold mb-2"),
                    P(
                        "The system has been initialized. You can now log in with your credentials.",
                        cls="text-lg opacity-90",
                    ),
                    Div(
                        "Redirecting to login...",
                        cls="mt-4 text-sm font-light italic animate-pulse",
                    ),
                    cls="success-msg alert alert-success text-white rounded-2xl shadow-2xl p-8 flex flex-col items-center justify-center w-full bg-gradient-to-br from-emerald-500 to-teal-600 border border-emerald-400/30 backdrop-blur-md animate-in fade-in zoom-in duration-500",
                    id="init-success",
                )
            )
        except Exception as e:
            # Manejo de error con fragmento HTML
            response = str(
                Div(
                    H1("Initialization Failed", cls="text-xl font-bold mb-1"),
                    P(str(e), cls="text-sm"),
                    cls="error-msg alert alert-error text-white rounded-xl shadow-lg p-4 flex flex-col items-center justify-center w-full bg-red-500/90 border border-red-400 animate-shake",
                    id="init-error",
                )
            )

        return Response(response)
