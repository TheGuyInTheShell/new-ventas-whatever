from fastapi_injectable import injectable
from core.config.settings import settings
import time
from typing import Union
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_async_db
from src.context.consts.jwt import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_MINUTES,
)

from ..users.models import User as UserModel
from core.lib.register.service import Service

from .schemas import CreateUser, User
from .types import TokenData

import bcrypt
from fastapi.security import OAuth2PasswordBearer
import jwt

import pyotp
import qrcode
import base64

from .exceptions import (
    handle_service_errors,
    handle_sync_errors,
    ServiceResult,
    AuthError,
    AuthenticationError,
    UserNotFoundError,
    UserAlreadyExistsError,
    TokenError,
    TokenExpiredError,
)


class HashContext:
    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )


class AuthService(Service):
    hash_context = HashContext()

    SECRET_KEY_JWT = settings.JWT_KEY.encode()
    USED_ALGORITHM = settings.JWT_ALG

    def generate_otp_secret(self) -> str:
        """Generates a random base32 formatted secret string."""
        return pyotp.random_base32()

    def verify_otp_code(self, secret: str, code: str) -> bool:
        """Verifies a TOTP code against the secret."""
        totp = pyotp.TOTP(secret)
        return totp.verify(code)

    def get_otp_provisioning_uri(
        self, secret: str, username: str, issuer_name: str = "FastAPI Template"
    ) -> str:
        """Generates the provisioning URI for the Authenticator app."""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=username, issuer_name=issuer_name)

    def generate_qr_code_base64(self, provisioning_uri: str) -> str:
        """Generates a QR code image encoded in base64."""
        import qrcode.image.svg
        from io import BytesIO

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        # Use SVG factory to avoid PIL dependency
        factory = qrcode.image.svg.SvgPathImage
        img = qr.make_image(image_factory=factory)

        buffered = BytesIO()
        img.save(buffered)

        # Return SVG base64 data URI
        return "data:image/svg+xml;base64," + base64.b64encode(
            buffered.getvalue()
        ).decode("utf-8")

    @injectable
    async def get_user(
        self, username: str, db: AsyncSession = Depends(get_async_db)
    ) -> UserModel:
        query = await UserModel.find_by_colunm(db, "username", username)
        user = query.scalar_one_or_none()
        if user is None:
            raise UserNotFoundError(f"User {username} not found")
        return user

    @handle_sync_errors
    def verify_password(
        self, plane_password: str, current_password: str
    ) -> ServiceResult[bool]:
        return (
            bcrypt.checkpw(
                plane_password.encode("utf-8"),
                current_password.encode("utf-8"),
            ),
            None,
        )

    @handle_service_errors
    async def authenticate_user(
        self, username: str, password: str
    ) -> ServiceResult[User]:
        user = await self.get_user(username)

        is_valid, error = self.verify_password(password, user.password)
        if error:
            return None, error
        if not is_valid:
            return None, AuthenticationError()

        user_schema = User(
            uid=user.uid,
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role_ref,
            otp_enabled=user.otp_enabled,
        )
        return user_schema, None

    @handle_service_errors
    async def create_user(
        self, db: AsyncSession, user_data: CreateUser
    ) -> ServiceResult[User]:
        user = await UserModel(
            username=user_data.username,
            password=bcrypt.hashpw(
                user_data.password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8"),
            email=user_data.email,
            full_name=user_data.full_name,
            role_ref=1,
        ).save(db)

        return (
            User(
                uid=user.uid,
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role_ref,
                otp_enabled=user.otp_enabled,
            ),
            None,
        )

    @handle_sync_errors
    def create_token(
        self, data: dict, expires_time: Union[float, None] = None
    ) -> ServiceResult[str]:
        current_time = int(time.time())
        if expires_time is None:
            expires = current_time + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        else:
            expires = current_time + int(expires_time)
        copy_user = data.copy()
        if "type" not in copy_user:
            copy_user["type"] = "access"
        copy_user.update({"exp": expires, "iat": current_time})
        token_jwt = jwt.encode(
            copy_user, key=self.SECRET_KEY_JWT, algorithm=self.USED_ALGORITHM
        )
        return token_jwt, None

    @handle_sync_errors
    def create_refresh_token(
        self, data: dict, expires_time: Union[float, None] = None
    ) -> ServiceResult[str]:
        current_time = int(time.time())
        if expires_time is None:
            expires = current_time + (REFRESH_TOKEN_EXPIRE_MINUTES * 60)
        else:
            expires = current_time + int(expires_time)
        copy_user = data.copy()
        copy_user.update({"exp": expires, "type": "refresh", "iat": current_time})
        token_jwt = jwt.encode(
            copy_user, key=self.SECRET_KEY_JWT, algorithm=self.USED_ALGORITHM
        )
        return token_jwt, None

    @handle_sync_errors
    def decode_token(self, token: str) -> ServiceResult[TokenData]:
        decode_cotent: dict = jwt.decode(
            token, key=self.SECRET_KEY_JWT, algorithms=[self.USED_ALGORITHM]
        )
        exp_time = decode_cotent.get("exp", 0)
        current_time = time.time()
        is_valid_time = exp_time > current_time
        if not is_valid_time:
            raise TokenExpiredError()

        return TokenData(**decode_cotent), None

    @injectable
    @handle_service_errors
    async def get_current_user(
        self,
        token: str = Depends(OAuth2PasswordBearer("auth/sign-in")),
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[User]:
        payload, error = self.decode_token(token)
        if error:
            return None, error
        if not payload:
            return None, TokenError("Empty payload")

        query = await UserModel.find_by_colunm(db, "username", payload.sub)
        user = query.scalar_one_or_none()
        if not user:
            return None, UserNotFoundError()

        return (
            User(
                uid=user.uid,
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role_ref,
                otp_enabled=user.otp_enabled,
            ),
            None,
        )
