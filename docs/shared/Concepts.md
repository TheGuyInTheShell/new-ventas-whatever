# Conceptos Core del Sistema

Este documento define las abstracciones fundamentales sobre las cuales se construye la arquitectura del sistema. Estos conceptos permiten la creación de un ecosistema altamente dinámico, desacoplado y polivalente.

---

## 1. Value (Valor)
Un **Value** es la unidad abstracta intercambiable más fundamental del sistema. No se limita a representar dinero; es cualquier elemento que puede ser cuantificado, poseído o transaccionado.

- **Naturaleza**: Agnostico. El sistema no juzga qué es el valor, solo que existe y se puede cuantificar.
- **Ejemplos**: Dinero (Fiat, Cripto), Comida (ingredientes, platillos pre-hechos), Tiempo (horas de servicio, reservas de una mesa), Servicios (consultorías, mano de obra), Productos físicos, Puntos de Lealtad, etc.
- **Propósito Arquitectónico**: Al abstraer el "qué" se está intercambiando, el núcleo del sistema no queda atado a una moneda o producto específico, permitiendo transacciones multidimensionales (ej. pagar un servicio entregando tiempo o comida).

## 2. Balance
El **Balance** representa la *cantidad de valores disponibles* en un contexto, entidad o contenedor específico (como un inventario, una billetera, una bodega o la cuenta de un usuario).

- **Limitación Conceptual**: No debe confundirse con el concepto estricto de contabilidad tradicional (partida doble, debe/haber o libros contables complejos). 
- **Propósito Arquitectónico**: Es puramente una medida instantánea de stock o disponibilidad para un *Value* particular. Responde a una pregunta simple pero crítica: *"¿Cuánto de la abstracción 'Value X' tenemos disponible aquí y ahora para usar o intercambiar?"*.

## 3. Comparison (Comparación / Tasa de Cambio)
La **Comparison** es el mecanismo que establece la relación de equivalencia y convertibilidad entre diferentes tipos de *Values*.

- **Definición**: Es la regla matemática o de negocio que determina que *"X cantidad del Valor A es equivalente a Y cantidad del Valor B"*.
- **Ejemplos**: 
  - 1 USD (Valor: Dinero) = 20 MXN (Valor: Dinero)
  - 1 Hora de Asesoría (Valor: Tiempo) = 50 USD (Valor: Dinero)
  - 2 Hamburguesas (Valor: Comida) = 1 Entrada de Cine (Valor: Servicio/Ticket)
- **Propósito Arquitectónico**: Actúa como el motor de intercambio subyacente. Permite que el sistema procese transacciones entre naturalezas completamente distintas de forma fluida y auditable.

---

## 4. Arquitectura de Datos: Líquida vs Sólida
Para lograr un sistema verdaderamente adaptable, la arquitectura de datos y la lógica de dominio se dividen en dos estados conceptuales:

### Base de Datos "Líquida" (Abstracción Pura)
Es el núcleo fundacional (core) del sistema. Consiste exclusivamente en entidades abstractas y flexibles (como *Value*, *Balance*, *Comparison*, *Transaction*, *Entity*).
- **Características**: Al ser "líquida", toma la forma del recipiente (el modelo de negocio). El core *no sabe* qué es un "restaurante", una "tienda de ropa", un "banco" o una "clínica". Solo sabe cómo procesar flujos y movimientos de valores de un balance a otro.
- **Ventaja**: Garantiza la reutilización extrema. Permite construir *cualquier* sistema de ventas o intercambio de recursos usando las mismas piezas fundamentales, reduciendo la deuda técnica al evitar la sobre-especialización prematura.

### Base de Datos "Sólida" (Especialización / Materialización)
Es la capa externa donde la abstracción líquida se congela o "solidifica" en requerimientos concretos de negocio, necesidades de la industria, o restricciones legales.
- **Características**: Aquí es donde un *Value* genérico adquiere propiedades concretas: se convierte en un "Impuesto (IVA)", un "Platillo Picante", o un "Descuento de Empleado". Aquí residen los esquemas de facturación fiscal exigidos por ley, la estructura de un menú, o los roles operativos (Mesero, Cajero).
- **Ventaja**: Mantiene el core (líquido) inmutable y limpio. Las reglas de negocio volátiles y específicas de un dominio (las partes sólidas) se implementan en capas superiores mediante metadatos, vistas, o relaciones específicas, facilitando el mantenimiento y la actualización.

---

## 5. El Resultado: Un Sistema POS Polivalente
Al amalgamar estos conceptos — *Values* abstractos, *Balances* agnósticos, *Comparisons* entre dimensiones distintas, y un núcleo *Líquido* que puede *Solidificarse* a demanda — el resultado arquitectónico es un **Sistema de Punto de Venta (POS) Polivalente**.

**¿Cómo se traduce esto en la práctica operativa?**

1. **Gestión Unificada de Recursos**: El "Inventario" (Balances) deja de ser solo para productos empaquetados. Puede gestionar ingredientes a granel, horas disponibles de los empleados, o mesas libres. Todo fluye a través de los mismos pipes de código.
2. **Transacciones Multidimensionales**: Un cliente en una cafetería podría pagar su cuenta total (Value: Dinero) usando un mix de métodos: tarjeta de crédito (Dinero), un saldo de referidos en la app (Puntos), y un cupón de compensación (Servicio). El motor de *Comparison* resuelve la matemática transaccional al vuelo.
3. **Escalabilidad Horizontal de Negocio (Pivotaje)**: Si la empresa decide que su sistema de restaurante ahora también debe gestionar las habitaciones del hotel boutique adjunto, los ingenieros no necesitan reescribir la lógica de cobro o inventario. Simplemente "solidifican" nuevas entidades (Habitaciones) sobre la misma base líquida. El POS se adapta al negocio, no al revés.
