- [ ] CI/CD con GitHub Actions
# FastAPI Template

Una plantilla completa y lista para producción para construir aplicaciones web modernas con FastAPI, incluyendo autenticación, gestión de permisos, WebSockets en tiempo real, y un panel administrativo.

## 🚀 Características Principales

### **Base de Datos y Rendimiento**
- **FastAPI**: Framework web moderno y de alto rendimiento para construir APIs con Python 3.11+
- **SQLAlchemy 2.0**: ORM potente con soporte completo para conexiones síncronas y asíncronas.
- **Optimización de Pool de Conexiones**: Ajuste fino de pooling (pre-ping, LIFO, gestión de tamaño/overflow) para entornos de alta concurrencia.
- **Warm-up de Base de Datos**: Lógica `warm_up_async_db` integrada para eliminar la latencia inicial (~1.5s) en arranques en frío.
- **Migraciones con Alembic**: Sistema robusto de control de versiones para la base de datos.
- **PostgreSQL**: Base de datos relacional con soporte nativo async/sync.
- **Pydantic 2.0**: Validación de datos y serialización de alta velocidad.

### **Frontend y Diseño Moderno**
- **Tailwind CSS 4.0**: El último framework CSS utility-first para un estilizado ultra rápido.
- **DaisyUI 5.0**: Librería de componentes UI premium para estéticas modernas.
- **Alpine.js 3.x (Modular)**: Lógica frontend reactiva organizada en módulos JavaScript mantenibles.
- **HTMX 2.0**: Potencia AJAX, WebSockets y Server Sent Events directamente en HTML.
- **ApexCharts**: Visualizaciones de datos interactivas y responsivas.
- **Iconos Lucide**: Iconografía limpia y consistente.
- **Rolldown**: Bundler de activos de próxima generación para un rendimiento óptimo.
- **Jinja2 Templates**: Generación dinámica de HTML con renderizado en el servidor.

### **Autenticación y Seguridad**
- **Sistema de Permisos Shield**: Sistema de seguridad declarativo que escanea rutas y sincroniza permisos automáticamente con la base de datos.
- **JWT (JSON Web Tokens)**: Autenticación segura basada en tokens.
- **Refresh Tokens**: Gestión de sesiones de larga duración (7 días por defecto).
- **Autenticación de Dos Factores (2FA/OTP)**: Soporte nativo para TOTP mediante Google Authenticator.
- **Roles y Permisos (RBAC)**: Control de acceso granular basado en roles.
- **Middleware de Verificación**: Pipeline automático de verificación de JWT y roles.

### **Arquitectura Modular**
- **Módulos de Negocio**: Amplia librería de módulos para Finanzas, ERP y gestión empresarial.
- **Auto-registro de Rutas**: Registro de rutas de API y Templates sin configuración manual.
- **Separación de Responsabilidades**: Clara distinción entre Controladores, Servicios, Modelos y Schemas.

### **Calidad de Código**
- **PEP 561 Compliance**: Soporte completo para tipado estático con `py.typed`.
- **Mypy Static Analysis**: Configuración integrada para garantizar la seguridad de tipos.
- **Prometheus**: Métricas y monitoreo en tiempo real de la aplicación.
- **APScheduler**: Programación avanzada de tareas en segundo plano.
- **Redis**: Caché y almacenamiento de sesiones de alto rendimiento.
- **Docker**: Contenedorización completa con Docker y Docker Compose.


## 📁 Estructura del Proyecto

```
.
├── core/                      # Núcleo de la aplicación (Lógica compartida)
│   ├── database/             # Configuración y drivers de BD
│   ├── security/             # Seguridad y sistema de permisos Shield
│   ├── lib/                  # Auto-registro y utilidades core
│   ├── middleware/           # Middlewares de FastAPI
│   └── events/               # Sistema asíncrono ChannelEvent
│
├── src/                       # Código fuente
│   ├── api/                  # Controladores de API (Routers FastAPI)
│   ├── app/                  # Frontend Web (Jinja2 + Alpine.js + HTMX)
│   │   ├── templates/        # Controladores de páginas
│   │   ├── partials/         # Controladores de componentes
│   │   └── web/              # Archivos estáticos y salida del bundler
│   ├── modules/              # Módulos basados en dominio
│   │   ├── auth/             # Lógica de autenticación
│   │   ├── balances/         # Finanzas: Gestión de balances
│   │   ├── invoices/         # Finanzas: Gestión de facturas
│   │   └── ...               # 20+ módulos adicionales
│   └── sockets/              # Manejadores de eventos en tiempo real
│
├── public/                    # Activos estáticos (Favicon, etc.)
├── plugins/                   # Sistema de plugins extensible
├── main.py                    # Punto de entrada de la aplicación
├── requirements.txt           # Dependencias de Python
├── package.json               # Dependencias y scripts de frontend
├── rolldown.config.mjs        # Configuración de empaquetado de activos
└── docker-compose.yaml        # Orquestación de servicios
```


## 🛠️ CLI - Generador de Módulos

Este proyecto incluye una **herramienta CLI** para generar módulos automáticamente con toda la estructura necesaria.

### Uso del Generador

**Generar un módulo simple:**
```bash
python cli.py generate:module products
```

Esto crea:
```
app/modules/products/
├── __init__.py
├── controller.py    # Router FastAPI con endpoints CRUD
├── schemas.py       # Schemas Pydantic (Request/Response)
├── models.py        # Modelo SQLAlchemy
└── services.py      # Lógica de negocio
```

**Generar módulos anidados:**
```bash
python cli.py generate:module store.inventory
```

Esto crea:
```
app/modules/store/
├── __init__.py
└── inventory/
    ├── __init__.py
    ├── controller.py
    ├── schemas.py
    ├── models.py
    └── services.py
```

### Archivos Generados

Cada módulo generado incluye:

- **controller.py**: Router completo con endpoints CRUD (GET, POST, PUT, DELETE)
- **schemas.py**: Schemas de Request/Response con paginación
- **models.py**: Modelo SQLAlchemy con campos básicos
- **services.py**: Funciones de servicio base

### Personalización Post-Generación

Después de generar un módulo:

1. **Editar `models.py`**: Añade los campos específicos de tu modelo
2. **Actualizar `schemas.py`**: Añade validaciones y campos necesarios
3. **Modificar `controller.py`**: Personaliza los endpoints según tus necesidades
4. **Implementar `services.py`**: Añade la lógica de negocio específica
5. **Registrar el router**: Importa y registra en `main.py` o usa auto-registro
6. **Ejecutar migraciones**: Crea y aplica migraciones de Alembic si modificaste modelos

## 🛠️ Instalación

### Prerrequisitos

- Python 3.11 o superior
- PostgreSQL 12 o superior
- Node.js y npm (para desarrollo frontend)
- Redis (opcional, para caché)
- Docker y Docker Compose (opcional)

### Opción 1: Instalación Local

1. **Clonar el repositorio**
```bash
git clone https://github.com/TheGuyInTheShell/fastapi-template.git
cd fastapi-template
```

2. **Crear y configurar el entorno virtual**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias de Python**
```bash
pip install -r requirements.txt
```

4. **Instalar dependencias de Node.js** (para Tailwind CSS)
```bash
npm install
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### **Migraciones de Base de Datos**
Este proyecto utiliza **Alembic** para gestionar los cambios en el esquema de la base de datos.

#### Comandos Útiles:
- **Generar una nueva migración automáticamente**:
  ```bash
  alembic revision --autogenerate -m "descripción del cambio"
  ```
- **Aplicar migraciones a la base de datos**:
  ```bash
  alembic upgrade head
  ```
- **Revertir la última migración**:
  ```bash
  alembic downgrade -1
  ```
- **Ver el historial de migraciones**:
  ```bash
  alembic history --verbose
  ```

Las configuraciones de Alembic se encuentran en `alembic.ini` y `migrations/env.py`. El sistema carga automáticamente la conexión desde tu archivo `.env`.

Configuración del archivo `.env`:
```env
# JWT Configuration
JWT_KEY=tu_clave_secreta_jwt_aqui
JWT_ALG=HS256

# Database Configuration
DB_NAME=nombre_base_datos
DB_USER=usuario_postgres
DB_PASSWORD=contraseña_postgres
DB_HOST=localhost
DB_PORT=5432

# Application Mode
MODE=DEBUG  # o PRODUCTION
```

6. **Crear la base de datos**
```bash
# Conectarse a PostgreSQL y crear la base de datos
psql -U postgres
CREATE DATABASE nombre_base_datos;
```

### Opción 2: Instalación con Docker

1. **Clonar el repositorio**
```bash
git clone https://github.com/TheGuyInTheShell/fastapi-template.git
cd fastapi-template
```

2. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env según sea necesario
```

3. **Construir y ejecutar con Docker Compose**
```bash
docker-compose up --build
```

La aplicación estará disponible en `http://localhost:8880`

Para habilitar los agentes de IA, asegúrate de configurar las claves de API necesarias en `.env`:
```env
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
```

## 🚀 Uso

### Desarrollo

**Iniciar el servidor de desarrollo:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Compilar Tailwind CSS en modo watch:**
```bash
nodemon
```

**Acceder a la documentación interactiva:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Métricas Prometheus: `http://localhost:8000/metrics`

### Producción

**Con Gunicorn:**
```bash
gunicorn -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000 --workers 4
```

**Con PM2 (usando ecosystem.config.js):**
```bash
pm2 start ecosystem.config.js
```

**Con Docker:**
```bash
docker-compose up -d
```

### Análisis Estático de Tipos

El proyecto utiliza `mypy` para garantizar la seguridad de tipos. Para ejecutar el análisis:

```bash
python -m mypy .
```

La configuración se encuentra en `mypy.ini`, la cual excluye automáticamente las plantillas del admin para evitar colisiones de nombres de módulos en los controladores.

## 📚 Módulos y Funcionalidades

El sistema está organizado en módulos especializados, siguiendo un diseño basado en el dominio que separa la infraestructura central de la lógica de negocio.

### 1. **Módulos de Infraestructura Core**

#### **Autenticación y Seguridad** (`src/modules/auth/`)
- **JWT Avanzado**: Generación segura de tokens con claims personalizados.
- **Refresh Tokens**: Renovación automática de sesiones vía `/auth/refresh`.
- **2FA/OTP**: Soporte nativo para Google Authenticator (generación de QR y verificación).
- **Shield Guard**: Verificación a nivel de middleware de roles y permisos.

#### **Gestión de Usuarios y Roles** (`src/modules/users/`, `src/modules/roles/`)
- **RBAC Jerárquico**: Herencia de roles y asignación de permisos flexible.
- **Perfiles de Usuario**: CRUD completo con paginación y filtrado automáticos.

#### **Menús Dinámicos** (`src/modules/menu/`)
- **Navegación basada en Roles**: Los menús se filtran dinámicamente según los permisos del usuario.
- **Estructura Jerárquica**: Soporte para elementos de menú anidados con iconos y ordenamiento.

### 2. **Módulos de Negocio y Finanzas**

#### **Balances y Transacciones** (`src/modules/balances/`, `src/modules/transactions/`)
- **Balances Globales**: Seguimiento en tiempo real de balances de divisas y activos.
- **Libro Mayor de Transacciones**: Procesamiento atómico con pistas de auditoría completas.
- **Sistema de Buffer**: `transactions_buffer` para la ingesta de transacciones de alta frecuencia.

#### **Facturación y Entidades** (`src/modules/invoices/`, `src/modules/business_entities/`)
- **Motor de Facturación**: Genera y gestiona facturas vinculadas a entidades de negocio.
- **Gestión de Entidades**: Administra Empresas (`business_entities`) e Individuos (`persons`).
- **Grupos de Entidades**: Categoriza y agrupa entidades para procesamiento masivo.

#### **Comparación y Valores** (`src/modules/values/`, `src/modules/comparison_values/`)
- **Métricas Dinámicas**: Sigue y compara valores a través de diferentes periodos o entidades.
- **Snapshots Históricos**: Toma de instantáneas automática para análisis de tendencias.

### 3. **Tiempo Real y Comunicación**

#### **WebSockets (Socket.IO)** (`src/sockets/`)
- **Basado en Eventos**: Comunicación bidireccional con namespaces y salas personalizadas.
- **Integración FastAPI**: Integración fluida con el ciclo de vida de la aplicación.

#### **Sistema de Webhooks** (`src/webhooks/`)
- **Entrantes/Salientes**: Sistema robusto para manejar integraciones externas.
- **ChannelEvent Hooks**: Procesamiento desacoplado mediante el sistema de eventos interno.

### 4. **IA y Extensiones** (`src/app/ext/`)
- **Agentes de IA**: Colaboración multi-agente utilizando LangChain y LangGraph.
- **Herramientas Personalizadas**: Herramientas específicas del dominio para que los agentes interactúen con el núcleo financiero.


## 🔧 Arquitectura y Patrones

### Arquitectura Modular

Cada módulo sigue una estructura consistente:

```
module_name/
├── controller.py    # Endpoints y rutas
├── services.py      # Lógica de negocio
├── models.py        # Modelos de base de datos
└── schemas.py       # Schemas Pydantic (validación)
```

### Auto-registro de Rutas

Las rutas se registran automáticamente siguiendo la estructura de carpetas:

```python
# core/utils/import_modules.py analiza la carpeta modules/
# y registra automáticamente todos los routers encontrados
```

### Middleware Pipeline

1. **CORS Middleware**: Configuración de orígenes permitidos
2. **JWT Verify**: Validación de tokens en rutas protegidas
3. **Role Verify**: Verificación de permisos basados en roles

### Conexiones de Base de Datos

**Asíncrona** (recomendada para endpoints):
```python
from core.database import get_async_db

@router.get("/")
async def endpoint(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

**Síncrona** (para inicialización):
```python
from core.database.sync_connection import engineSync
BaseSync.metadata.create_all(engineSync)
```

### Sistema de Eventos (ChannelEvent)

El núcleo de la comunicación asíncrona es `ChannelEvent`, que permite:

1. **Suscrube/Listen**: Decoradores `@channel.subscribe_to` y `@channel.listen_to`.
2. **Inyección de Dependencias**: Uso de `result = channel.DependsEvent(event_result)` para recibir resultados de eventos previos.
3. **Inyección Inteligente**: Los suscriptores reciben automáticamente el argumento `result` si lo declaran en su firma.
4. **Resiliencia**: Inicialización robusta de eventos y manejo de errores.

## 🔐 Seguridad

### Mejores Prácticas Implementadas

1. **Contraseñas Hasheadas**: Uso de bcrypt para hash seguro
2. **JWT con Expiración**: Tokens con tiempo de vida limitado
3. **CORS Configurado**: Control de orígenes permitidos
4. **Validación de Entrada**: Pydantic valida todos los datos de entrada
5. **SQL Injection Protection**: SQLAlchemy ORM previene inyecciones SQL
6. **Variables de Entorno**: Credenciales sensibles en archivos .env

### Generar Clave JWT Segura

```python
import secrets
jwt_key = secrets.token_hex(32)
print(jwt_key)
```

## 📊 Base de Datos y Rendimiento

### **Optimización de Conexiones**
El proyecto implementa una estrategia de conexión de alto rendimiento:
- **Warm-up de Pool**: Al iniciar la aplicación, se ejecuta una tarea `warm_up_async_db` para establecer las conexiones iniciales, evitando la sobrecarga en la primera petición del usuario.
- **Parámetros Optimizados**:
    - `pool_size=10` / `max_overflow=20`
    - `pool_pre_ping=True` (resiliencia contra conexiones inactivas)
    - `pool_use_lifo=True` (mejora la tasa de acierto en caché)
    - `pool_recycle=1800` (previene timeouts del lado del servidor de BD)

### **Modelos Principales**
- **Core de Finanzas**: `Balance`, `Transaction`, `Invoice`, `BusinessEntity`, `Person`.
- **Identidad y Acceso**: `User`, `Role`, `Permission`, `Menu`.
- **Sistema**: `Options` (Configuración dinámica), `ApiToken`.

### **Migraciones**
El proyecto utiliza **Alembic** para el control de versiones del esquema. Las tablas se sincronizan automáticamente durante la configuración inicial mediante el hook `Base.metadata.create_all`, pero se recomienda el uso de Alembic para actualizaciones en entornos de producción.


## 🎨 Panel Administrativo

El panel administrativo incluye:

- **Dashboard**: Vista general del sistema
- **Gestión de Usuarios**: CRUD completo
- **Gestión de Roles y Permisos**: Asignación visual
- **Configuración de Menús**: Editor de menús
- **Logs y Monitoreo**: Visualización de logs

**Acceso**: `http://localhost:8000/admin`

## 📈 Monitoreo y Métricas

### Prometheus

Métricas disponibles en `/metrics`:

- Número de peticiones
- Latencia de respuestas
- Errores HTTP
- Uso de recursos

### Integración con Grafana

```yaml
# Ejemplo de configuración para Grafana
datasources:
  - name: Prometheus
    type: prometheus
    url: http://localhost:8000/metrics
```

## 🧪 Testing

### Estructura de Tests (Recomendada)

```
tests/
├── test_auth.py
├── test_users.py
├── test_roles.py
└── conftest.py
```

### Ejemplo de Test

```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_sign_up():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/auth/sign-up", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        })
        assert response.status_code == 201
```

## 🌐 Despliegue

### Variables de Entorno para Producción

```env
MODE=PRODUCTION
JWT_KEY=clave_super_segura_de_produccion
DB_HOST=db.produccion.com
DB_PASSWORD=contraseña_segura
```

### Nginx como Reverse Proxy

```nginx
server {
    listen 80;
    server_name api.tudominio.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /sio/ {
        proxy_pass http://localhost:8000/sio/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Systemd Service

```ini
[Unit]
Description=FastAPI Application
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/fastapi_template
ExecStart=/path/to/venv/bin/gunicorn -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está licenciado bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte

- **Documentación FastAPI**: https://fastapi.tiangolo.com/
- **Documentación SQLAlchemy**: https://docs.sqlalchemy.org/
- **Documentación Socket.IO**: https://socket.io/docs/
- **Repositorio**: https://github.com/TheGuyInTheShell/fastapi-template

## 🎯 Próximas Características

- [ ] Conexion SMTP
- [ ] Rate limiting por usuario
- [ ] Tests completos
- [ ] Soporte para múltiples idiomas (i18n)

---

**Desarrollado con ❤️ usando FastAPI**
