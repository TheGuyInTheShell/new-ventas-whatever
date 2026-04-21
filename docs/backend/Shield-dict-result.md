# Resultado del Diccionario de Permisos (Shield Registry)

Este documento detalla la estructura del diccionario resultante generado por el sistema de seguridad **Shield**, específicamente a través de la clase `PermissionRegistry`.

## Estructura del Diccionario

El diccionario es una representación jerárquica de los permisos registrados, organizados por **contextos**. La raíz del diccionario contiene una lista de nodos de contexto principales.

### Ejemplo de Estructura (JSON)

```json
{
  "permissions": [
    {
      "permissions": [
        {
          "name": "system.init",
          "action": "execute",
          "type": "shield",
          "description": "Permite la ejecución del proceso de inicialización del sistema",
          "context": "core.system",
          "meta": {
            "key": "priority",
            "value": "critical"
          }
        }
      ],
      "childs": [
        {
          "permissions": [],
          "childs": []
        }
      ]
    }
  ]
}
```

## Componentes y Anotaciones de Tipo

La estructura se basa en las siguientes definiciones de tipos encontradas en `core/security/shield/types.py`:

### 1. `PermissionRegistry.to_dict()`
Es el punto de entrada para obtener la representación de datos.
- **Retorno**: `Dict[str, List[Dict[str, Any]]]`
- **Clave principal**: `"permissions"` (Lista de nodos de contexto raíz).

### 2. `PermissionNode`
Representa un nivel o "Namespace" dentro de la jerarquía de permisos.
- **Anotación**: `dataclass`
- **Campos en el diccionario**:
  - `permissions`: `List[PermissionDefinition]` (Permisos directos de este contexto).
  - `childs`: `List[PermissionNode]` (Nodos de contextos hijos).

### 3. `PermissionDefinition`
Representa un permiso individual y sumetadata.
- **Anotación**: `dataclass(frozen=True, slots=True)`
- **Campos en el diccionario**:
  - `name` (`str`): Identificador único del permiso.
  - `action` (`str`): Operación que protege (ej: `read`, `write`, `execute`).
  - `type` (`str`): Categoría del escudo.
  - `description` (`str`): Texto descriptivo para auditoría o UI.
  - `context` (`str`): El namespace completo del permiso.
  - `meta` (`PermissionMeta`): Objeto de metadatos adicionales.

### 4. `PermissionMeta`
Par clave-valor para información extendida.
- **Campos**: `key` (`str`), `value` (`str`).

---

## Lógica de Consolidación

El registro (`PermissionRegistry`) utiliza un patrón **Singleton** para asegurar que todos los escudos (`shields`) definidos en la aplicación se registren en una única fuente de verdad. 

1. **Escaneo**: Durante el arranque, los decoradores `@Shield` envían definiciones al registro.
2. **Jerarquía**: Si se define un `parent_context`, el registro vincula el nodo actual como hijo del padre correspondiente, construyendo el árbol que se ve en el `to_dict()`.
3. **Validación**: No se admiten colisiones (mismo nombre y tipo en el mismo contexto).
