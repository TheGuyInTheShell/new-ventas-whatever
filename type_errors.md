# Python Type Errors (ty diagnostics)

Total: 103 diagnostics

## Categoría: Dependencias Faltantes
- [ ] **pytest**: No está en `pyproject.toml`.
  - `src\tests\unitaries\test_business_entities_services.py:1:8`
  - `src\tests\unitaries\test_comparison_value_decorators_services.py:1:8`
  - ... y otros tests.

## Categoría: Importaciones Relativas Fallidas
- [ ] **`src\domain\services\transaction_and_invoice.py`**: Uso de `...modules`.
- [ ] **`src\domain\services\value_with_comparison.py`**: Uso de `...modules`.

## Categoría: Errores de Retorno (Type Mismatch)
- [ ] **`src\modules\auth\services.py`**: Retorna valores simples cuando se espera `tuple[Result | None, BaseError | None]`.
- [ ] **`src\modules\users\services.py`**: Retorna `User` o `None` cuando se espera la tupla de resultado.

## Categoría: Atributos no Encontrados (Modelos)
- [ ] **`User`**: Falta `password` y `role_ref`.
- [ ] **`MetaPermissions`**, **`MetaUsers`**: Faltan métodos `find_one`, `delete`.

## Categoría: SQLAlchemy / Sesiones
- [ ] **`verify_search_business_service.py`**: Problemas con `sessionmaker` y `async with`.

---

# Plan de Ataque

1. **Fijar dependencias**: Instalar y agregar `pytest` a `dev`.
2. **Normalizar importaciones**: Cambiar importaciones relativas ambiguas por rutas absolutas o relativas correctas.
3. **Corregir firmas de retorno**: Asegurar que los servicios devuelvan la tupla `(resultado, error)`.
4. **Actualizar modelos/interfaces**: Agregar atributos faltantes o usar `getattr` si son dinámicos.
