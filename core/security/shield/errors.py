class ShieldPermissionError(Exception):
    """El usuario no tiene el permiso requerido."""
    def __init__(self, name: str, type_str: str, context: str):
        self.name = name
        self.type = type_str
        self.context = context
        super().__init__(f"No permission for '{name}' of type '{type_str}' in context '{context}'")


class ShieldRegistryError(Exception):
    """Error de registro de permisos (duplicados, contexto inválido, etc.)."""
    pass
