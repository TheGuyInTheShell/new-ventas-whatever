from fastapi_injectable import injectable
from core.config.settings import settings
import time
from typing import Union
from fastapi import HTTPException, Depends
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_async_db

from ..users.models import User as UserModel
from core.lib.register.service import Service

from .schemas import CreateUser, User
from .types import TokenData

import bcrypt
from bcrypt import _bcrypt  # type: ignore
from fastapi.security import OAuth2PasswordBearer
import jwt

import pyotp
import qrcode
import base64


if not hasattr(bcrypt, "__about__"):
    setattr(
        bcrypt,
        "__about__",
        type("About", (object,), {"__version__": _bcrypt.__version_ex__}),
    )


class AuthService(Service):

    SECRET_KEY_JWT = settings.JWT_KEY.encode()
    USED_ALGORITHM = settings.JWT_ALG

    ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes
    REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

    hash_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
    ) -> User | None:
        try:
            query = await UserModel.find_by_colunm(db, "username", username)
            user = query.scalar_one_or_none()
            return user
        except ValueError as e:
            print(e)
            return None

    def verify_password(self, plane_password: str, current_password: str) -> bool:
        return self.hash_context.verify(plane_password, current_password)

    @injectable
    async def authenticade_user(self, username: str, password: str) -> User | None:
        try:
            user = await self.get_user(username)
            if user is None:
                return None
            same_passowords = self.verify_password(password, user.password)
            if same_passowords is False:
                return None
            result = User(
                uid=user.uid,
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role_ref,
                otp_enabled=user.otp_enabled,
            )
            return result
        except ValueError as e:
            print(e)
            return None

    async def create_user(self, db: AsyncSession, user_data: CreateUser) -> dict | None:
        try:

            user = await UserModel(
                username=user_data.username,
                password=self.hash_context.hash(user_data.password),
                email=user_data.email,
                full_name=user_data.full_name,
                role_ref=1,
            ).save(db)

            return {
                "uid": user.uid,
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role_ref,
            }
        except ValueError as e:
            print(e)
            return None

    def create_token(self, data: dict, expires_time: Union[float, None] = None) -> str:
        current_time = int(time.time())
        if expires_time is None:
            expires = current_time + (self.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        else:
            expires = current_time + int(expires_time)
        copy_user = data.copy()
        if "type" not in copy_user:
            copy_user["type"] = "access"
        copy_user.update({"exp": expires, "iat": current_time})
        token_jwt = jwt.encode(
            copy_user, key=self.SECRET_KEY_JWT, algorithm=self.USED_ALGORITHM
        )
        return token_jwt

    def create_refresh_token(
        self, data: dict, expires_time: Union[float, None] = None
    ) -> str:
        current_time = int(time.time())
        if expires_time is None:
            expires = current_time + (self.REFRESH_TOKEN_EXPIRE_MINUTES * 60)
        else:
            expires = current_time + int(expires_time)
        copy_user = data.copy()
        copy_user.update({"exp": expires, "type": "refresh", "iat": current_time})
        token_jwt = jwt.encode(
            copy_user, key=self.SECRET_KEY_JWT, algorithm=self.USED_ALGORITHM
        )
        return token_jwt

    def decode_token(self, token: str) -> TokenData | None:
        try:
            decode_cotent: dict = jwt.decode(
                token, key=self.SECRET_KEY_JWT, algorithms=[self.USED_ALGORITHM]
            )
            exp_time = decode_cotent.get("exp", 0)
            current_time = time.time()
            is_valid_time = exp_time > current_time
            if not is_valid_time:
                return None

            return TokenData(**decode_cotent)
        except Exception as e:
            return None

    @injectable
    async def get_current_user(
        self,
        token: str = Depends(OAuth2PasswordBearer("auth/sign-in")),
        db: AsyncSession = Depends(get_async_db),
    ) -> User | None:
        payload = self.decode_token(token)
        if not payload:
            return None
        query = await UserModel.find_by_colunm(db, "username", payload.sub)
        user = query.scalar_one_or_none()
        if not user:
            return None
        return user
