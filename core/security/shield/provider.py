from abc import ABC, abstractmethod

class ResolverProvider(ABC):
    """
    Contrato abstracto para la resolución de permisos en runtime.
    El consumidor debe heredar de esta clase y suministrar la lógica
    que determina si el contexto/usuario actual tiene el permiso.
    """

    @abstractmethod
    def resolve(self, name: str, type_str: str, context: str) -> bool:
        """
        Resuelve si el usuario/sesión actual tiene el permiso solicitado.
        Retorna True si tiene permiso, False de lo contrario.
        
        Args:
            name: Nombre del permiso (ej. 'users:read')
            type_str: Tipo de permiso (ej. 'endpoint', 'argument')
            context: Contexto del permiso (ej. 'UsersController')
        """
        pass
