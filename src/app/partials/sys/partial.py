from core.lib.decorators import Get, Post, Services
from core.lib.register import Partial
from typing import Annotated

from src.modules.users.services import UsersService
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_async_db
from fastapi import Depends, Form as FastAPIForm
from fastapi.responses import Response
from fastcore.xml import Div, H1, P, I, to_xml
from core.security.csrf.csrf import CSRF
from core.security.shield.shield import Shield
from src.modules.auth.shields import SysInitShield


@Services(UsersService)
@Shield.register(context="System")
class SysPartials(Partial):
    """Controlador de parciales para el sistema."""

    UsersService: "UsersService"

    @Post("/init", response_class=Response)
    @Shield.need(
        name="sys",
        action="init",
        type="partial",
        description="Permite ejecutar la inicialización del sistema.",
        resolver=SysInitShield(),
    )
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
            response = to_xml(
                Div(
                    Div(
                        Div(
                            I(
                                data_lucide="party-popper",
                                cls="w-12 h-12 text-white mb-6",
                            ),
                            H1(
                                "Owner Created Successfully",
                                cls="text-3xl font-black mb-2 tracking-tight",
                            ),
                            P(
                                "The master vault has been initialized and secured.",
                                cls="text-lg opacity-80 font-medium mb-6",
                            ),
                            Div(
                                Div(
                                    Div(
                                        cls="loading loading-ring loading-md text-white/50"
                                    ),
                                    P(
                                        "Redirecting to login protocol...",
                                        cls="text-sm font-bold tracking-widest uppercase text-white/40",
                                    ),
                                    cls="flex items-center gap-3 mt-4",
                                ),
                                cls="pt-6 border-t border-white/10 w-full flex justify-center",
                            ),
                            cls="flex flex-col items-center text-center",
                        ),
                        cls="relative z-10",
                    ),
                    # Subtle background patterns
                    Div(
                        cls="absolute -top-24 -right-24 w-64 h-64 bg-white/10 rounded-full blur-3xl"
                    ),
                    Div(
                        cls="absolute -bottom-24 -left-24 w-64 h-64 bg-emerald-400/20 rounded-full blur-3xl"
                    ),
                    cls="success-msg relative overflow-hidden text-white rounded-[2.5rem] p-12 flex flex-col items-center justify-center w-full bg-gradient-to-br from-emerald-600 to-teal-700 border border-white/20 shadow-[0_20px_50px_rgba(16,185,129,0.3)] animate-in fade-in zoom-in duration-700",
                    id="init-success",
                )
            )
        except Exception as e:
            print(e)
            # Manejo de error con fragmento HTML
            response = to_xml(
                Div(
                    I(data_lucide="alert-octagon", cls="w-10 h-10 text-white mb-4"),
                    H1(
                        "Initialization Failed",
                        cls="text-xl font-black mb-1 uppercase tracking-wider",
                    ),
                    P(
                        str(e),
                        cls="text-sm font-medium opacity-90 bg-black/20 p-4 rounded-xl border border-white/10 mt-2",
                    ),
                    cls="error-msg text-white rounded-3xl shadow-2xl p-8 flex flex-col items-center justify-center w-full bg-gradient-to-br from-red-600 to-rose-700 border border-red-400/50 animate-shake",
                    id="init-error",
                )
            )
        return Response(response)
