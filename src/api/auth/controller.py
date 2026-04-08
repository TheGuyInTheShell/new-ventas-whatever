from datetime import datetime
from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.lib.decorators import Get, Post
from core.lib.register import Controller
from src.modules.users.models import User

from src.modules.auth.schemas import RQUser, RQUserLogin, RSUser, RSUserTokenData, OTPEnableRequest
from src.modules.auth.types import TokenData
from src.modules.auth.services import (
    authenticade_user,
    create_refresh_token,
    create_token,
    create_user,
    decode_token,
    get_user,
    REFRESH_TOKEN_EXPIRE_MINUTES,
    get_current_user
)
from src.modules.auth.otp import generate_otp_secret, verify_otp_code, get_otp_provisioning_uri, generate_qr_code_base64
from pydantic import BaseModel


class OTPVerifyRequest(BaseModel):
    otp_code: str
    temp_token: str


class AuthController(Controller):
    """
    Controller for Authentication and 2FA.
    
    Path: /api/v1/auth
    """

    oauth2_schema = OAuth2PasswordBearer("auth/sign-in")

    @Get("/")
    def token(self, token: str = Depends(oauth2_schema)):
        return token

    @Post("/sign-in")
    async def sign_in(self, user_data: RQUserLogin, db: AsyncSession = Depends(get_async_db)):
        try:
            user = await authenticade_user(
                db, username=user_data.username, password=user_data.password
            )
            if user is None:
                raise HTTPException(
                    status_code=401, detail="Incorrect username or password"
                )

            if user.otp_enabled:
                temp_token = create_token(
                    data={
                        "sub": user.username,
                        "id": user.id,
                        "uid": user.uid,
                        "type": "partial_2fa",
                        "role": "guest"
                    }, 
                    expires_time=300
                )
                return JSONResponse(
                    status_code=202,
                    content={
                        "message": "OTP required",
                        "temp_token": temp_token,
                        "require_2fa": True
                    }
                )

            access_token = create_token(
                data={
                    "sub": user.username,
                    "email": user.email,
                    "role": user.role,
                    "full_name": user.full_name,
                    "id": user.id,
                    "uid": user.uid,
                }
            )

            refresh_token = create_refresh_token(
                data={
                    "sub": user.username,
                    "email": user.email,
                    "role": user.role,
                    "full_name": user.full_name,
                    "id": user.uid,
                }
            )

            response = JSONResponse(
                content={
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                }
            )

            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                samesite="lax",
            )

            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                max_age=REFRESH_TOKEN_EXPIRE_MINUTES * 60,
                path="/auth/refresh",
                samesite="lax",
            )

            return response
        except ValueError as e:
            print(e)
            raise e

    @Post("/refresh")
    async def refresh_token_endpoint(
        self, request: Request, response: Response, refresh_token: Optional[str] = Cookie(None)
    ):
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token missing")

        token_data = decode_token(refresh_token)

        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        if token_data.type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        username = token_data.sub
        email = token_data.email
        role = token_data.role
        full_name = token_data.full_name

        new_access_token = create_token(
            data={
                "sub": username,
                "email": email,
                "role": role,
                "full_name": full_name,
                "id": token_data.id,
                "uid": token_data.uid,
            }
        )

        response = JSONResponse(
            content={"access_token": new_access_token, "token_type": "bearer"}
        )

        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            samesite="lax",
        )

        return response

    @Post("/verify-otp")
    async def verify_otp(self, request: OTPVerifyRequest, db: AsyncSession = Depends(get_async_db)):
        payload = decode_token(request.temp_token)
        if not payload or payload.type != "partial_2fa":
            raise HTTPException(status_code=401, detail="Invalid session")
        
        user_id = payload.id
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid session")

        user = await User.find_one(db, user_id)
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
            
        if not user.otp_enabled:
            raise HTTPException(status_code=400, detail="2FA not enabled for user")

        if not verify_otp_code(user.otp_secret, request.otp_code):
            raise HTTPException(status_code=401, detail="Invalid OTP code")
            
        access_token = create_token(
                data={
                    "sub": user.username,
                    "email": user.email,
                    "role": user.role,
                    "full_name": user.full_name,
                    "id": user.id,
                    "uid": user.uid,
                }
            )
        
        refresh_token = create_refresh_token(
                data={
                    "sub": user.username,
                    "email": user.email,
                    "role": user.role,
                    "full_name": user.full_name,
                    "id": user.uid,
                }
            )

        response = JSONResponse(
                content={
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                }
            )

        response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                samesite="lax",
            )

        response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                max_age=REFRESH_TOKEN_EXPIRE_MINUTES * 60,
                path="/auth/refresh",
                samesite="lax",
            )
            
        return response

    @Get("/2fa/setup")
    async def setup_2fa(self, current_user=Depends(get_current_user)):
        secret = generate_otp_secret()
        uri = get_otp_provisioning_uri(secret, current_user.username)
        qr_b64 = generate_qr_code_base64(uri)
        
        return {
            "secret": secret,
            "qr_code": qr_b64
        }

    @Post("/2fa/enable")
    async def enable_2fa(self, request: OTPEnableRequest, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
        if verify_otp_code(request.secret, request.otp_code):
            current_user.otp_secret = request.secret
            current_user.otp_enabled = True
            await current_user.save(db)
            return {"message": "2FA enabled successfully"}
        else:
            raise HTTPException(status_code=400, detail="Invalid OTP code")

    @Post("/2fa/disable")
    async def disable_2fa(self, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
        current_user.otp_enabled = False
        current_user.otp_secret = None
        await current_user.save(db)
        return {"message": "2FA disabled successfully"}

    @Post("/sign-up")
    async def sign_up(
        self, form_sign_up: RQUser, db: AsyncSession = Depends(get_async_db)
    ) -> RSUser:
        try:
            query = await User.find_by_colunm(db, "username", form_sign_up.username)
            exists_user = query.scalar_one_or_none()
            if exists_user:
                raise HTTPException(
                    status_code=401,
                    detail="Nombre de usuario tomado",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            result = await create_user(db, form_sign_up)
            if not result:
                raise HTTPException(status_code=500, detail="Error al crear el usuario")
            return RSUser(
                uid=result.get("uid") or "",
                id=result.get("id") or 0,
                username=result.get("username") or "",
                role=result.get("role") or "",
                full_name=result.get("full_name") or "",
                email=result.get("email") or "",
            )
        except ValueError as e:
            print(e)
            raise e
