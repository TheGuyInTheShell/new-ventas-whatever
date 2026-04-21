from core.lib.decorators import Post, Services
from core.lib.register import Partial

from src.modules.auth.services import AuthService
from src.modules.users.services import UsersService
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_async_db
from fastapi import Depends, Form as FastAPIForm
from fastapi.responses import HTMLResponse
from fasthtml.common import Div, to_xml
from typing import Annotated
from core.security.csrf.csrf import CSRF


@Services(AuthService, UsersService)
class SignPartial(Partial):

    AuthService: "AuthService"
    # UserService: "UsersService"

    @Post("/in", response_class=HTMLResponse)
    @CSRF(["form"])
    async def sign_in_partial(
        self,
        username: Annotated[str, FastAPIForm()],
        password: Annotated[str, FastAPIForm()],
    ) -> HTMLResponse:

        user = await self.AuthService.authenticade_user(username, password)

        if user is None:
            content = to_xml(
                Div(
                    "Incorrect username or password",
                    role="alert",
                    cls="alert alert-error text-white text-sm font-semibold rounded-lg shadow-md p-3 animate-pulse flex items-center justify-center w-full",
                )
            )
            return HTMLResponse(content=content, status_code=200)

        expires_time = 1200
        access_token = self.AuthService.create_token(
            data={
                "sub": user.username,
                "email": user.email,
                "role": user.role,
                "full_name": user.full_name,
                "id": user.id,
            },
            expires_time=expires_time,
        )

        refresh_token = self.AuthService.create_refresh_token(
            data={
                "sub": user.username,
                "email": user.email,
                "role": user.role,
                "full_name": user.full_name,
                "id": user.id,
            }
        )

        content = to_xml(
            Div(
                f"Login successful! Redirecting...",
                role="alert",
                cls="success-msg alert alert-success text-white text-sm font-semibold rounded-lg shadow-md p-3 animate-bounce flex items-center justify-center w-full",
            )
        )

        response = HTMLResponse(content=content, status_code=200)

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            path="/auth/refresh",
        )

        response.headers["HX-Location"] = "/dashboard"
        return response
