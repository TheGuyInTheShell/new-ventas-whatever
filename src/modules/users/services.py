from fastapi import Request
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from core.lib.decorators.services import Services
from core.database import get_async_db
from fastapi.security import OAuth2PasswordBearer
from fastapi_injectable import injectable

from .models import User as UserModel
from .schemas import User as UserSchema
from ..auth.services import AuthService
from ..roles.services import RolesService
from ..options.services import OptionsService
from ..auth.exceptions import TokenError, AuthError, UserNotFoundError
from core.lib.decorators.exceptions import handle_service_errors, ServiceResult


@Services(AuthService, RolesService, OptionsService)
class UsersService(Service):
    AuthService: AuthService
    RolesService: RolesService
    OptionsService: OptionsService

    @injectable
    @handle_service_errors
    async def get_current_user_app(
        self,
        request: Request,
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[UserSchema]:
        """
        Obtiene el usuario actual desde el token JWT de la request.
        """
        auth_header = request.cookies.get("access_token")
        if not auth_header:
            return None

        payload, error = self.AuthService.decode_token(auth_header)
        if error or not payload:
            return None, TokenError("Token inválido")

        # Buscar el usuario en la base de datos
        query = await UserModel.find_by_colunm(db, "username", payload.sub)
        user = query.scalar_one_or_none()

        if not user:
            return None, UserNotFoundError()

        # Retornar el schema Pydantic con los datos del usuario
        return UserSchema(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            role=user.role_ref,
            otp_enabled=user.otp_enabled,
            created_at=user.created_at,
        )

    @injectable
    @handle_service_errors
    async def get_current_user_api(
        self,
        token: str = Depends(OAuth2PasswordBearer("auth/sign-in")),
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[UserSchema]:
        """
        Obtiene el usuario actual desde el token JWT de la request.
        """
        # Decodificar el token JWT
        payload, error = self.AuthService.decode_token(token)
        if error or not payload:
            return None, TokenError("Token inválido")

        # Buscar el usuario en la base de datos
        query = await UserModel.find_by_colunm(db, "username", payload.sub)
        user = query.scalar_one_or_none()

        if not user:
            return None, UserNotFoundError()

        # Retornar el schema Pydantic con los datos del usuario
        return UserSchema(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            role=user.role_ref,
            otp_enabled=user.otp_enabled,
            created_at=user.created_at,
        )

    @injectable
    @handle_service_errors
    async def create_owner(
        self,
        username: str,
        password: str,
        email: str,
        full_name: str,
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[UserModel]:
        """
        Crea el primer usuario owner del sistema y marca la inicialización como lista.
        """
        # 1. Obtener rol owner
        role = await self.RolesService.get_role_by_name("owner")
        if not role:
            # Si no existe, intentamos buscar Admin o usamos el ID 1 como fallback si es necesario,
            # pero lo ideal es que el rol Owner esté pre-creado.
            role = await self.RolesService.get_role_by_name("admin")
            if not role:
                return None, AuthError("Owner role not found in system")

        # 2. Hashear password
        hashed_password = self.AuthService.hash_context.hash(password)

        # 3. Crear usuario
        new_user = UserModel(
            username=username,
            password=hashed_password,
            email=email,
            full_name=full_name,
            role_ref=role.id,
        )

        await new_user.save(db)

        # 4. Crear opción de sistema
        await self.OptionsService.create_options(
            context="system_init", name="owner_signup", value="ready"
        )

        return new_user
