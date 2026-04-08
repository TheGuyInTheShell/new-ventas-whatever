from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from core.lib.decorators.services import Services
from core.database import get_async_db
from fastapi.security import OAuth2PasswordBearer
from fastapi_injectable import injectable

from .models import User
from .schemas import RSUser
from ..auth.services import AuthService


@Services(AuthService)
class UsersService(Service):
    AuthService: AuthService

    @injectable
    async def get_current_user(
        self,
        token: str = Depends(OAuth2PasswordBearer("auth/sign-in")),
        db: AsyncSession = Depends(get_async_db)
    ) -> RSUser:
        """
        Obtiene el usuario actual desde el token JWT de la request.
        """
        # Decodificar el token JWT
        payload = self.AuthService.decode_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        # Buscar el usuario en la base de datos
        query = await User.find_by_colunm(db, "username", payload.sub)
        user = query.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        
        # Retornar el schema Pydantic con los datos del usuario
        return RSUser(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            role=user.role_ref,
            otp_enabled=user.otp_enabled,
            created_at=user.created_at,
        )

