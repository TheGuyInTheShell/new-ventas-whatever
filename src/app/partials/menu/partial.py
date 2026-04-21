from core.lib.decorators import Get, Services
from core.lib.register import Partial

from src.modules.auth.services import AuthService
from src.modules.users.services import UsersService
from fastapi.responses import HTMLResponse
from fasthtml.common import Div, to_xml
from core.security.shield.shield import Shield


@Services(AuthService, UsersService)
@Shield.register(context="Menu")
class MenuPartial(Partial):

    AuthService: "AuthService"
    UserService: "UsersService"

    @Get("/", response_class=HTMLResponse)
    @Shield.need(
        name="menu",
        action="read",
        type="ui",
        description="Permite la ejecución del proceso de inicialización del sistema",
    )
    async def get_menu_partial(
        self,
    ) -> HTMLResponse:

        content = to_xml(
            Div(
                "Example menu",
                role="alert",
                cls="bg-primary-500",
            )
        )

        response = HTMLResponse(content=content, status_code=200)

        return response
