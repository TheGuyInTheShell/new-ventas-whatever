from core.lib.decorators import Get, Post, Services
from core.lib.register.partial import Partial
# from src.modules.auth.services import AuthService
# from src.modules.users.services import UsersService
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_async_db
from fastapi import Depends, Form as FastAPIForm
from fastapi.responses import Response
from fasthtml.common import *
from typing import Annotated
from core.security.csrf.csrf import CSRF

# @Services(AuthService, UsersService)
class SignPartial(Partial):

    # AuthService: "AuthService"
    # UserService: "UsersService"


    @Post("/in", response_class=Response)
    @CSRF(['form'])
    async def sign_in_partial(self, username: Annotated[str, FastAPIForm()], password: Annotated[str, FastAPIForm()], db: AsyncSession = Depends(get_async_db)) -> Response:
        
        # user = await self.AuthService.authenticade_user(db, username, password)

        # if user is None:
        #     return Div(
        #         "Incorrect username or password",
        #         cls="alert alert-error text-white text-sm font-semibold rounded-lg shadow-md p-3 animate-pulse flex items-center justify-center w-full"
        #     )

        # expires_time = 1200
        # access_token = self.AuthService.create_token(
        #     data={
        #         "sub": user.username,
        #         "email": user.email,
        #         "role": user.role,
        #         "full_name": user.full_name,
        #         "id": user.id,
        #     },
        #     expires_time=expires_time,
        # )

        # refresh_token = self.AuthService.create_refresh_token(
        #     data={
        #         "sub": user.username,
        #         "email": user.email,
        #         "role": user.role,
        #         "full_name": user.full_name,
        #         "id": user.id,
        #     }
        # )

        response = str(Div(
            f"Login successful! Redirecting... {username} {password}",
            cls="success-msg alert alert-success text-white text-sm font-semibold rounded-lg shadow-md p-3 animate-bounce flex items-center justify-center w-full"
        ))
        # response.set_cookie(
        #     key="access_token",
        #     value=access_token,
        #     httponly=True,
        #     secure=True,
        #     samesite="lax",
        # )
        # response.set_cookie(
        #     key="refresh_token",
        #     value=refresh_token,
        #     httponly=True,
        #     secure=True,
        #     samesite="lax",
        #     path="/auth/refresh",
        # )
        return Response(response)


