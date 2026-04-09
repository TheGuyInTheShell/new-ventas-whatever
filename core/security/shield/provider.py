from abc import ABC, abstractmethod
from typing import Any, Coroutine

class ResolverProvider(ABC):
    """
    Contrato abstracto para la resolución de permisos en runtime.
    El consumidor debe heredar de esta clase y suministrar la lógica
    que determina si el contexto/usuario actual tiene el permiso.
    """

    @abstractmethod
    def resolve(self, name: str, type_str: str, action: str, context: str, **kwargs: Any) -> bool | Coroutine[Any, Any, bool]:
        """
        Resuelve si el usuario/sesión actual tiene el permiso solicitado.
        Retorna True si tiene permiso, False de lo contrario.
        
        Args:
            name: Nombre del permiso (ej. 'users:read')
            type_str: Tipo de permiso (ej. 'endpoint', 'argument')
            context: Contexto del permiso (ej. 'UsersController')
        """
        pass

class BasicProvider(ABC):
    """
    Contrato abstracto simplificado que recibe unicamente la peticion.
    Ideal para validaciones de api keys u origin blocks a nivel primario.
    """

    @abstractmethod
    def resolve(self, request: Any) -> bool | Coroutine[Any, Any, bool]:
        """
        Resuelve si la peticion es autorizada. Retorna True o False.
        """
        pass
