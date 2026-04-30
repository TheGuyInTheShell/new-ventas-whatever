# Propuestas de Escalabilidad Arquitectónica: Modular Monolith 2.0

Este documento resume las directrices y decisiones de diseño tomadas para transformar el ecosistema de **Finance App** en una arquitectura robusta, predecible y mantenible por equipos de alta performance.

## 1. El Patrón `ServiceResult` (Value, Error)
Para evitar que la lógica de negocio esté salpicada de excepciones de infraestructura (`HTTPException`), adoptamos una firma de retorno estandarizada en todos los servicios:

```python
# Mal: Lógica de negocio lanzando errores HTTP 400
# Bien: Retorno de contrato explícito
async def my_service(...) -> ServiceResult[MyModel]:
    if not valid:
        return None, DomainError("Motivo de negocio")
    return data, None
```

### Ventajas:
- **Testabilidad**: Los tests unitarios no necesitan capturar excepciones para validar errores de negocio.
- **Transparencia**: El flujo de control es lineal (`if error: return`), no oculto tras un stack trace.
- **Desacoplamiento**: El servicio no sabe que vive en un entorno FastAPI/HTTP.

---

## 2. Orquestación de Transacciones en el Controlador
Las transacciones de base de datos (`db.commit()`, `db.rollback()`) deben vivir en la capa de **Controlador**, no dentro de los servicios individuales.

- **Servicios**: Realizan operaciones atómicas sobre el `AsyncSession` (usando `db.flush()` si es necesario para obtener IDs).
- **Controladores**: Actúan como la frontera de la transacción. Si un controlador llama a dos servicios, ambos deben completarse antes de hacer un solo `commit()`.

### Regla de Oro:
> Un servicio NUNCA debe hacer commit por sí mismo, a menos que sea una operación de "fire and forget" totalmente aislada.

---

## 3. Estrategia Anti-N+1: Proyecciones y Carga Explícita
Para evitar la degradación de performance en entornos de alta carga, eliminamos la dependencia en el "Lazy Loading" (que a menudo falla en contextos asíncronos o genera cientos de queries).

### Proyecciones Explícitas (RS-Schemas):
- Cada endpoint debe devolver un esquema de respuesta (`RSValue`, `RSOrder`) específico.
- El mapeo de Modelo ORM a Pydantic debe ocurrir en el **Servicio** antes de que el objeto salga de su frontera.

### Eager Loading Parametrizado:
Los métodos base (`find_one`, `find_all`) han sido extendidos para aceptar un parámetro `options`. Los servicios deben pasar explícitamente qué relaciones necesitan cargar:

```python
# Ejemplo en el Servicio
values = await Value.find_all(db, options=[selectinload(Value.meta)])
```

---

## 4. "Grep-abilidad" sobre Magia Dinámica
En sistemas complejos, la capacidad de encontrar dónde se usa un campo o se genera un esquema es vital.

- **Evitar Generadores Dinámicos**: No usar herramientas que generen esquemas Pydantic al vuelo desde SQLAlchemy si eso impide el "Find in Files".
- **Contratos Explícitos**: Preferimos escribir 20 líneas de esquema manuales que usar un decorador "mágico" que oculte qué campos se están exponiendo.

---

## 5. Frontend: Arquitectura de Islas Interactivas
Para mantener la simplicidad del SSR (Server Side Rendering) sin sacrificar la interactividad moderna:

- **HTMX**: Para el 80% de las interacciones (navegación, formularios, swaps de fragmentos HTML).
- **XState / Alpine.js**: Para las "Islas de Interactividad" (inventarios complejos, calculadoras en tiempo real) donde el estado es demasiado denso para viajar continuamente al servidor.
- **Sincronización vía Eventos**: Uso de `HX-Trigger` para comunicar cambios entre el servidor y las máquinas de estado del frontend.

---

## 6. Mantenimiento y Evolución
1. **Migrations**: Siempre usar Alembic. Nunca confiar en `Base.metadata.create_all`.
2. **Glosario de Dominios**: Mantener los módulos (`src/modules/`) aislados. Si el Módulo A necesita datos del Módulo B, debe hacerlo a través del Servicio de B, no accediendo directamente a sus modelos.
3. **Logging**: Usar el decorador `@handle_service_errors` para asegurar que cualquier excepción no controlada sea capturada, logueada con traceback y devuelta como un error de sistema limpio.
