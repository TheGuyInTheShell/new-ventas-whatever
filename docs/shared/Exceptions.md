# Metodología de Captura de Errores (Value, Error)

Este proyecto utiliza una metodología de manejo de errores explícita basada en el patrón de retorno de tuplas `(Value, Error)`, inspirada en lenguajes como Go. Esta aproximación garantiza que los errores sean tratados como ciudadanos de primera clase y deban ser gestionados explícitamente por los consumidores de los servicios.

## 📋 Conceptos Clave

### 1. El Tipo `ServiceResult`
Cada método de servicio debe devolver una tupla que contiene opcionalmente el resultado exitoso y opcionalmente un objeto de excepción.

```python
ServiceResult[T] = tuple[Optional[T], Optional[BaseError]]
```

### 2. Decoradores de Automatización
Para simplificar la implementación y garantizar que ningún error inesperado rompa la aplicación, utilizamos decoradores que envuelven la lógica del servicio.

- **`@handle_service_errors`**: Para métodos asíncronos (`async def`).
- **`@handle_sync_errors`**: Para métodos síncronos (`def`).

Estos decoradores:
1. Ejecutan el método.
2. Si tiene éxito, devuelven `(resultado, None)`.
3. Si ocurre una excepción conocida (e.g., `AuthError`), devuelven `(None, error)`.
4. Si ocurre una excepción inesperada, la registran en los logs (con traceback) y devuelven `(None, SystemError)`.

---

## 🛠️ Guía de Uso

### En el Servicio
Al definir métodos en un servicio, se debe tipar el retorno con `ServiceResult` y aplicar el decorador correspondiente. No es necesario usar bloques `try/except` internos a menos que se quiera manejar una lógica de recuperación específica.

```python
from .exceptions import handle_service_errors, ServiceResult, UserNotFoundError

class MyService(Service):
    
    @handle_service_errors
    async def get_item(self, item_id: int) -> ServiceResult[Item]:
        item = await db.get(Item, item_id)
        if not item:
            # Podemos retornar el error manualmente o dejar que el decorador lo capture si lanzamos excepción
            return None, UserNotFoundError()
        
        return item # El decorador lo transformará en (item, None)
```

### En el Consumidor (Controladores/Partials)
El consumidor **debe** desempaquetar la tupla y verificar si existe un error antes de proceder.

```python
async def my_controller(self, item_id: int):
    item, error = await self.MyService.get_item(item_id)
    
    if error:
        # Manejo explícito del error
        return HTMLResponse(f"Error: {error.message}", status_code=400)
    
    # Uso seguro del valor
    return render_template("item.html", item=item)
```

---

## 🚀 Beneficios
1. **Flujo de Control Explícito**: No hay "saltos" inesperados en el código debido a excepciones lanzadas que nadie atrapa.
2. **Seguridad de Tipos**: El programador sabe exactamente qué puede fallar.
3. **Observabilidad**: Todas las excepciones no controladas se registran automáticamente con contexto (nombre de clase y método).
4. **Desacoplamiento**: El servicio no necesita saber nada sobre HTTP o el transporte; simplemente informa qué salió mal.
