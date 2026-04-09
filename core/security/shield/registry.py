from typing import Dict, Optional, Any
from .types import PermissionDefinition, PermissionNode
from .errors import ShieldRegistryError

class PermissionRegistry:
    """Almacén singleton de permisos, organizado jerárquicamente por contexto."""
    
    _root: PermissionNode
    _context_index: Dict[str, PermissionNode]

    def __init__(self) -> None:
        self.clear()

    def clear(self) -> None:
        """Limpia todo el registro (útil para testing o reinicios)."""
        self._root = PermissionNode()
        self._context_index = {}

    def get_node(self, context: str, create_if_missing: bool = False) -> Optional[PermissionNode]:
        """Obtiene un PermissionNode por su contexto exacto."""
        if context in self._context_index:
            return self._context_index[context]
        
        if create_if_missing:
            node = PermissionNode()
            self._context_index[context] = node
            return node
        
        return None

    def add(self, definition: PermissionDefinition, parent_context: Optional[str] = None) -> None:
        """
        Registra un permiso en el árbol.
        Si parent_context es None (o es el mismo que dictionary parent), 
        se vincula al root temporalmente hasta que se construya con scan, 
        pero para facilitar el diseño, manejamos todo como un grafo indexado y luego montamos la jerarquía.
        """
        context = definition.context
        
        # Validar duplicados exactos en el mismo contexto
        node = self.get_node(context, create_if_missing=True)
        if node is not None:
            for p in node.permissions:
                if p.name == definition.name and p.type == definition.type:
                    raise ShieldRegistryError(f"Permiso '{definition.name}' de tipo '{definition.type}' ya registrado en contexto '{context}'")
            node.permissions.append(definition)

            # Link al padre si está explícito para construir la estructura jerárquica luego
            if parent_context and parent_context != context:
                parent_node = self.get_node(parent_context, create_if_missing=True)
                if parent_node is not None and context not in parent_node.childs:
                    parent_node.childs[context] = node
            elif parent_context is None:
                # Si no hay un padre claro, se ata al root global inicialmente
                if context not in self._root.childs:
                    self._root.childs[context] = node

    def to_dict(self) -> Dict[str, Any]:
        """Genera el diccionario completo de permisos a nivel raíz."""
        # Se retornan los hijos del root aplanando un nivel o iterando
        return {
            "permissions": [node.to_dict() for node in self._root.childs.values()]
        }

# Instancia global (singleton pattern para facilidad de uso de los decoradores)
permission_registry = PermissionRegistry()
