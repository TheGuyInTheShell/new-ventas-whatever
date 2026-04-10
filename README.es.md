- [ ] CI/CD con GitHub Actions
# FastAPI Template

Una plantilla completa y lista para producción para construir aplicaciones web modernas con FastAPI, incluyendo autenticación, gestión de permisos, WebSockets en tiempo real, y un panel administrativo.

## 🚀 Características Principales

### **Base de Datos y Modelado**
- **FastAPI**: Framework web moderno y de alto rendimiento para construir APIs con Python 3.11+
- **SQLAlchemy**: ORM potente con soporte para conexiones síncronas y asíncronas
- **Migraciones con Alembic**: Sistema de control de versiones para la base de datos
- **PostgreSQL**: Base de datos relacional con soporte completo async/sync
- **Pydantic**: Validación de datos y serialización automática

### **Autenticación y Seguridad**
- **JWT (JSON Web Tokens)**: Sistema de autenticación basado en tokens
- **Refresh Tokens**: Soporte para renovación de sesiones mediante tokens de larga duración (7 días por defecto)
- **Autenticación de Dos Factores (2FA/OTP)**: Capa extra de seguridad mediante Google Authenticator o similares
- **OAuth2**: Implementación de flujo OAuth2 con Password Bearer
- **Sistema de Roles y Permisos**: Control de acceso basado en roles (RBAC)
- **Generación Automática de Permisos**: Los permisos se generan automáticamente por cada endpoint
- **Middleware de Verificación**: Verificación de JWT y roles en cada petición

### **Comunicación en Tiempo Real**
- **Socket.IO**: Comunicación bidireccional y basada en eventos entre cliente y servidor
- **Eventos Asíncronos**: Sistema de eventos `ChannelEvent` con soporte de inyección de dependencias (`DependsEvent`) y resultados.
- **WebSocket Support**: Soporte completo para conexiones WebSocket
- **Webhooks System**: Sistema robusto de Webhooks entrantes y salientes con registro automático.

### **Extensiones e IA** (ejemplo de uso)
- **AI Agents**: Integración con LangChain y LangGraph para lógica compleja "ejemplo".
- **Arquitectura de Agentes**: Soporte para grafos multi-agente, herramientas personalizadas y memoria "ejemplo".

### **Panel Administrativo**
- **Interfaz de Administración**: Panel web para gestionar recursos de la API
- **Tailwind CSS**: Framework CSS utility-first para diseños personalizados
- **Jinja2 Templates**: Motor de plantillas para generar páginas HTML dinámicas
- **Gestión de Menús**: Sistema de menús dinámicos basado en roles

### **Arquitectura Modular**
- **Estructura por Módulos**: Organización clara y escalable del código
- **Auto-registro de Rutas**: Las rutas se registran automáticamente siguiendo la estructura de carpetas
- **Separación de Responsabilidades**: Controllers, Services, Models, y Schemas separados

### **Calidad de Código y Tipado**
- **PEP 561 Compliance**: El proyecto incluye markers `py.typed` para soporte completo de editores y herramientas de tipado.
- **Mypy Static Analysis**: Configuración de `mypy` integrada para garantizar la seguridad de tipos.
- **Tipado Estándar**: Uso de `async_sessionmaker[AsyncSession]` y otros tipos modernos de Python.
- **Prometheus**: Métricas y monitoreo de la aplicación integrado
- **APScheduler**: Programación de tareas asíncronas y trabajos en segundo plano
- **Redis**: Caché y almacenamiento de sesiones
- **Nodemon**: Recarga automática durante el desarrollo
- **Docker**: Contenedorización completa con Docker y Docker Compose

## 📁 Estructura del Proyecto

```
fastapi_template/
├── core/                      # Núcleo de la aplicación
│   ├── database/             # Configuración de base de datos
│   │   ├── drivers/          # Drivers de base de datos
│   │   │   └─── postgresql/   # Driver de PostgreSQL
│   ├── py.typed              # Marker de tipado PEP 561
│   └── utils/                # Utilidades de base de datos (paginación, etc.)
│   ├── middlewares/          # Middlewares personalizados
│   │   ├── jwt_verify.py         # Verificación de tokens JWT
│   │   └── role_verify.py        # Verificación de permisos por rol
│   ├── jobs/                 # Tareas programadas con APScheduler
│   ├── routes/               # Configuración de rutas principales
│   ├── services/             # Servicios compartidos
│   ├── schemas/              # Schemas Pydantic compartidos
│   ├── cache/                # Sistema de caché con Redis
│   ├── event/                # Sistema de eventos personalizado
│   └── utils/                # Utilidades generales
│
├── app/                       # Directorio principal de la aplicación
│   ├── modules/               # Módulos de funcionalidad
│   │   ├── auth/             # Autenticación (sign-in, sign-up)
│   │   ├── users/            # Gestión de usuarios
│   │   ├── roles/            # Gestión de roles
│   │   ├── permissions/      # Gestión de permisos
│   │   ├── tokens/           # Gestión de tokens API
│   │   └── menu/             # Sistema de menús dinámicos
│   │
│   ├── sockets/               # WebSockets y Socket.IO
│   │   ├── __init__.py       # Inicialización de eventos Socket.IO
│   │   └── live/             # Eventos en tiempo real
│   │
│   └── public/                # Archivos públicos estáticos
│
├── admin/                     # Panel administrativo
│   ├── src/                  # Plantillas Jinja2
│   ├── static/               # Archivos estáticos (CSS, JS, imágenes)
│   ├── templates/            # Configuración de plantillas
│   └── global/               # Configuración global del admin
├── logs/                      # Archivos de registro
├── main.py                    # Punto de entrada de la aplicación
├── requirements.txt           # Dependencias Python
├── Dockerfile                 # Configuración Docker
├── docker-compose.yaml        # Orquestación de servicios
├── .env.example              # Ejemplo de variables de entorno
└── ER_db_diagram.dbml        # Diagrama de base de datos
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

### 1. **Módulo de Autenticación** (`modules/auth/`)

Gestiona el registro e inicio de sesión de usuarios.

**Endpoints:**
- `POST /auth/sign-up` - Registrar nuevo usuario
- `POST /auth/sign-in` - Iniciar sesión y obtener token JWT
- `GET /auth/` - Verificar token

**Características:**
- Encriptación de contraseñas con bcrypt
- Generación de tokens JWT con expiración configurable
- Validación de credenciales
- Prevención de usuarios duplicados
- **Refresh Tokens**: Endpoint `/auth/refresh` para obtener nuevos tokens de acceso sin re-autenticar
- **2FA/OTP**: Soporte para autenticación de dos factores mediante:
    - `GET /auth/2fa/setup` - Genera secreto y código QR
    - `POST /auth/2fa/enable` - Activa 2FA para el usuario
    - `POST /auth/verify-otp` - Verifica el código OTP durante el login
    - `POST /auth/2fa/disable` - Desactiva 2FA

### 2. **Módulo de Usuarios** (`modules/users/`)

Gestión completa de usuarios del sistema.

**Endpoints:**
- `GET /users/me` - Obtener datos del usuario autenticado
- `GET /users/` - Listar todos los usuarios (con paginación)
- `GET /users/id/{id}` - Obtener usuario por ID
- `PUT /users/id/{id}` - Actualizar usuario
- `DELETE /users/id/{id}` - Eliminar usuario

**Características:**
- Paginación automática
- Filtrado y búsqueda
- Relación con roles
- Validación de datos con Pydantic

### 3. **Módulo de Roles** (`modules/roles/`)

Sistema de roles para control de acceso.

**Endpoints:**
- `GET /roles/` - Listar roles
- `GET /roles/id/{id}` - Obtener rol por ID
- `POST /roles/` - Crear nuevo rol
- `PUT /roles/id/{id}` - Actualizar rol
- `DELETE /roles/id/{id}` - Eliminar rol

**Características:**
- Roles jerárquicos
- Asignación de permisos a roles
- Relación muchos a muchos con permisos

### 4. **Módulo de Permisos** (`modules/permissions/`)

Gestión granular de permisos.

**Endpoints:**
- `GET /permissions/` - Listar permisos
- `GET /permissions/id/{id}` - Obtener permiso por ID
- `POST /permissions/` - Crear permiso
- `PUT /permissions/id/{id}` - Actualizar permiso
- `DELETE /permissions/id/{id}` - Eliminar permiso

**Características:**
- **Generación automática**: Los permisos se crean automáticamente al iniciar la aplicación basándose en las rutas registradas
- Control de acceso por endpoint
- Asignación flexible a roles

### 5. **Módulo de Tokens API** (`modules/tokens/`)

Gestión de tokens de API para integraciones.

**Endpoints:**
- `GET /tokens/` - Listar tokens
- `GET /tokens/id/{id}` - Obtener token por ID
- `POST /tokens/` - Crear nuevo token
- `PUT /tokens/id/{id}` - Actualizar token
- `DELETE /tokens/id/{id}` - Eliminar token

### 6. **Módulo de Menús** (`modules/menu/`)

Sistema de menús dinámicos basado en roles.

**Endpoints:**
- `GET /menu/` - Listar menús
- `GET /menu/id/{id}` - Obtener menú por ID
- `POST /menu/` - Crear menú
- `PUT /menu/id/{id}` - Actualizar menú
- `DELETE /menu/id/{id}` - Eliminar menú

**Características:**
- Menús jerárquicos (padres e hijos)
- Asignación por roles
- Iconos y ordenamiento personalizado

### 7. **WebSockets y Socket.IO** (`sockets/`)

Comunicación en tiempo real.

**Características:**
- Eventos personalizados
- Rooms y namespaces
- Autenticación de conexiones
- Broadcast de mensajes
- Integración con FastAPI

**Ejemplo de uso:**
```python
# Servidor (sockets/live/events.py)
@sio.on('mensaje')
async def handle_mensaje(sid, data):
    await sio.emit('respuesta', {'data': 'recibido'}, room=sid)
```

### 8. **Sistema de Caché** (`core/cache/`)

Caché con Redis para mejorar el rendimiento.

**Características:**
- Almacenamiento en caché de consultas frecuentes
- TTL configurable
- Invalidación de caché

### 9. **Tareas Programadas** (`core/jobs/`)

Ejecución de tareas en segundo plano con APScheduler.

**Características:**
- Tareas cron
- Tareas por intervalo
- Tareas únicas
- Tareas únicas
- Gestión del ciclo de vida

### 10. **Sistema de Webhooks** (`app/webhooks/`)

Sistema centralizado para manejar webhooks de entrada y salida.

**Estructura:**
- `in/`: Controladores para recibir webhooks de servicios externos.
- `out/`: Suscriptores que escuchan eventos internos y envían datos a servicios externos.

**Características:**
- **Auto-descubrimiento**: Los controladores y suscriptores se cargan automáticamente.
- **ChannelEvent Integrado**: Desacoplamiento total mediante eventos.
- **Validación**: Uso de Pydantic para validar payloads entrantes.

### 11. **Extensiones e IA** (`app/ext/`)

Carpeta dedicada a lógica de negocio compleja y agentes de IA.

**Estructura (`app/ext/ia/`):**
- `agents/`: Definición de agentes (Researcher, Writer, etc.)
- `graphs/`: Flujos de trabajo con LangGraph (StateGraph, MultiAgentGraph)
- `tools/`: Herramientas personalizadas para los agentes
- `chains/`: Cadenas de procesamiento LangChain

**Ejemplo de uso (LangGraph):**
El sistema incluye un ejemplo de grafo multi-agente donde un investigador y un escritor colaboran para generar contenido.

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

## 📊 Base de Datos

### Modelos Principales

- **User**: Usuarios del sistema
- **Role**: Roles de usuario
- **Permission**: Permisos granulares
- **Menu**: Elementos del menú
- **MenuRole**: Relación menú-rol
- **ApiToken**: Tokens de API

### Migraciones

El proyecto crea las tablas automáticamente al iniciar:

```python
# En main.py
BaseSync.metadata.create_all(engineSync)
BasicBaseAsync.metadata.create_all(engineSync)
```

Para migraciones más avanzadas, considera usar **Alembic**:

```bash
pip install alembic
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

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
