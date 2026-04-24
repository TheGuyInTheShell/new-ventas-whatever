# FastAPI Template

A complete, production-ready template for building modern web applications with FastAPI, including authentication, permission management, real-time WebSockets, and an administrative panel.

### 🚀 Key Features

### **Database and Performance**
- **FastAPI**: Modern, high-performance web framework for building APIs with Python 3.11+
- **SQLAlchemy 2.0**: Powerful ORM with support for both synchronous and asynchronous connections.
- **Connection Pool Optimization**: Fine-tuned pooling (pre-ping, LIFO, size/overflow management) for high-concurrency environments.
- **Database Warm-up**: Integrated `warm_up_async_db` logic to eliminate the initial request latency (~1.5s) on cold starts.
- **Alembic Migrations**: Robust database version control system.
- **PostgreSQL**: Relational database with full async/sync support.
- **Pydantic 2.0**: High-speed data validation and automatic serialization.

### **Frontend and Design**
- **Tailwind CSS 4.0**: The latest utility-first CSS framework for lightning-fast styling.
- **DaisyUI 5.0**: Premium UI component library for modern aesthetics.
- **Alpine.js 3.x (Modular)**: Reactive frontend logic organized into maintainable JavaScript modules.
- **HTMX 2.0**: High-power AJAX, WebSockets, and Server Sent Events directly in HTML.
- **ApexCharts**: Interactive and responsive data visualizations.
- **Lucide Icons**: Clean and consistent iconography.
- **Rolldown**: Next-generation asset bundler for optimal performance.
- **Jinja2 Templates**: Dynamic HTML generation with server-side rendering.

### **Authentication and Security**
- **Shield Permission System**: Declarative security system that automatically scans routes and syncs permissions to the DB.
- **JWT (JSON Web Tokens)**: Secure token-based authentication.
- **Refresh Tokens**: Long-lived session management (7 days by default).
- **Two-Factor Authentication (2FA/OTP)**: Native support for TOTP via Google Authenticator.
- **Roles and Permissions (RBAC)**: Granular Role-Based Access Control.
- **Verification Middleware**: Automatic JWT and role verification pipeline.

### **Modular Architecture**
- **Business-First Modules**: Extensive library of modules for Finance, ERP, and Business management.
- **Automatic Route Registration**: Zero-config API and Template route registration.
- **Separation of Concerns**: Clean separation between Controllers, Services, Models, and Schemas.

### **Code Quality and Type Safety**
- **PEP 561 Compliance**: Full static typing support with `py.typed`.
- **Mypy Static Analysis**: Integrated type checking configuration.
- **Prometheus**: Real-time application metrics and monitoring.
- **APScheduler**: Advanced scheduling for background jobs.
- **Redis**: High-performance cache and session storage.
- **Docker**: Full containerization with Docker and Docker Compose.

## 📁 Project Structure

```
.
├── core/                      # Application core (Shared Logic)
│   ├── database/             # Database configuration & drivers
│   ├── security/             # Security & Shield permission system
│   ├── lib/                  # Auto-registration & core utilities
│   ├── middleware/           # FastAPI Middlewares
│   └── events/               # ChannelEvent async system
│
├── src/                       # Source code
│   ├── api/                  # API Controllers (FastAPI Routers)
│   ├── app/                  # Web Frontend (Jinja2 + Alpine.js + HTMX)
│   │   ├── templates/        # Page controllers
│   │   ├── partials/         # Component controllers
│   │   └── web/              # Static files & bundler output
│   ├── modules/              # Domain-driven modules
│   │   ├── auth/             # Authentication logic
│   │   ├── balances/         # Finance: Balances management
│   │   ├── invoices/         # Finance: Invoice management
│   │   └── ...               # 20+ additional modules
│   └── sockets/              # Real-time event handlers
│
├── public/                    # Static assets (Favicon, etc.)
├── plugins/                   # Extensible plugin system
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── package.json               # Frontend dependencies & scripts
├── rolldown.config.mjs        # Asset bundling configuration
├── Dockerfile                 # Docker configuration
└── docker-compose.yaml        # Service orchestration
```

## 🛠️ CLI - Module Generator

This project includes a **CLI tool** to automatically generate modules with all the necessary structure.

### Using the Generator

**Generate a simple module:**
```bash
python cli.py generate:module products
```

This creates:
```
app/modules/products/
├── __init__.py
├── controller.py    # FastAPI Router with CRUD endpoints
├── schemas.py       # Pydantic Schemas (Request/Response)
├── models.py        # SQLAlchemy Model
└── services.py      # Business Logic
```

**Generate nested modules:**
```bash
python cli.py generate:module store.inventory
```

This creates:
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

### Generated Files

Each generated module includes:

- **controller.py**: Full Router with CRUD endpoints (GET, POST, PUT, DELETE)
- **schemas.py**: Request/Response Schemas with pagination
- **models.py**: SQLAlchemy Model with basic fields
- **services.py**: Base service functions

### Post-Generation Customization

After generating a module:

1. **Edit `models.py`**: Add your model's specific fields
2. **Update `schemas.py`**: Add necessary validations and fields
3. **Modify `controller.py`**: Customize endpoints to your needs
4. **Implement `services.py`**: Add specific business logic
5. **Register the router**: Import and register in `main.py` or use auto-registration
6. **Run migrations**: Create and apply Alembic migrations if you modified models

## 🛠️ Installation

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 12 or higher
- Node.js and npm (for frontend development)
- Redis (optional, for cache)
- Docker and Docker Compose (optional)

### Option 1: Local Installation

1. **Clone the repository**
```bash
git clone https://github.com/TheGuyInTheShell/fastapi-template.git
cd fastapi-template
```

2. **Create and configure the virtual environment**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

4. **Install Node.js dependencies** (for Tailwind CSS)
```bash
npm install
```

5. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your settings
```

### **Database Migrations**
This project uses **Alembic** to manage database schema changes.

#### Useful Commands:
- **Generate a new migration automatically**:
  ```bash
  alembic revision --autogenerate -m "change description"
  ```
- **Apply migrations to the database**:
  ```bash
  alembic upgrade head
  ```
- **Revert the last migration**:
  ```bash
  alembic downgrade -1
  ```
- **View migration history**:
  ```bash
  alembic history --verbose
  ```

Alembic configurations are found in `alembic.ini` and `migrations/env.py`. The system automatically loads the connection from your `.env` file.

`.env` file configuration:
```env
# JWT Configuration
JWT_KEY=your_jwt_secret_key_here
JWT_ALG=HS256

# Database Configuration
DB_NAME=database_name
DB_USER=postgres_user
DB_PASSWORD=postgres_password
DB_HOST=localhost
DB_PORT=5432

# Application Mode
MODE=DEBUG  # or PRODUCTION
```

6. **Create the database**
```bash
# Connect to PostgreSQL and create the database
psql -U postgres
CREATE DATABASE database_name;
```

### Option 2: Installation with Docker

1. **Clone the repository**
```bash
git clone https://github.com/TheGuyInTheShell/fastapi-template.git
cd fastapi-template
```

2. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env as needed
```

3. **Build and run with Docker Compose**
```bash
docker-compose up --build
```

The application will be available at `http://localhost:8880`

To enable AI agents, make sure to configure the necessary API keys in `.env`:
```env
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
```

## 🚀 Usage

### Development

**Start the development server:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Compile Tailwind CSS in watch mode:**
```bash
nodemon
```

**Access interactive documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Prometheus Metrics: `http://localhost:8000/metrics`

### Production

**With Gunicorn:**
```bash
gunicorn -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000 --workers 4
```

**With PM2 (using ecosystem.config.js):**
```bash
pm2 start ecosystem.config.js
```

**With Docker:**
```bash
docker-compose up -d
```

### Static Type Analysis

The project uses `mypy` to ensure type safety. To run the analysis:

```bash
python -m mypy .
```

The configuration is in `mypy.ini`, which automatically excludes admin templates to avoid module name collisions in controllers.

## 📚 Modules and Features

The system is organized into specialized modules, following a domain-driven design that separates core infrastructure from business logic.

### 1. **Core Infrastructure Modules**

#### **Authentication & Security** (`src/modules/auth/`)
- **Advanced JWT**: Secure token generation with custom claims.
- **Refresh Tokens**: Automated session renewal via `/auth/refresh`.
- **2FA/OTP**: native Google Authenticator support (QR generation and verification).
- **Shield Guard**: Middleware-level verification of roles and permissions.

#### **User & Role Management** (`src/modules/users/`, `src/modules/roles/`)
- **Hierarchical RBAC**: Flexible role inheritance and permission assignment.
- **User Profiles**: Full CRUD with automated pagination and filtering.

#### **Dynamic Menus** (`src/modules/menu/`)
- **Role-Based Navigation**: Menus are filtered dynamically based on user permissions.
- **Hierarchical Structure**: Supports nested menu items with icons and custom ordering.

### 2. **Business & Finance Modules**

#### **Balances & Transactions** (`src/modules/balances/`, `src/modules/transactions/`)
- **Global Balances**: Real-time tracking of currency and asset balances.
- **Transaction Ledger**: Atomic transaction processing with full audit trails.
- **Buffer System**: `transactions_buffer` for high-frequency transaction ingestion.

#### **Invoicing & Entities** (`src/modules/invoices/`, `src/modules/business_entities/`)
- **Invoicing Engine**: Generate and manage invoices linked to business entities.
- **Entity Management**: Manage Companies (`business_entities`) and Individuals (`persons`).
- **Entity Groups**: Categorize and group entities for bulk processing.

#### **Comparison & Values** (`src/modules/values/`, `src/modules/comparison_values/`)
- **Dynamic Metrics**: Track and compare values across different timeframes or entities.
- **Historical Snapshots**: Automated snapshotting for trend analysis.

### 3. **Real-Time & Communication**

#### **WebSockets (Socket.IO)** (`src/sockets/`)
- **Event-Driven**: Bi-directional communication with custom namespaces and rooms.
- **FastAPI Integration**: Seamless integration with the main application lifecycle.

#### **Webhooks System** (`src/webhooks/`)
- **Incoming/Outgoing**: Robust system for handling external integrations.
- **ChannelEvent Hooks**: Decoupled processing via the internal event system.

### 4. **AI & Extensions** (`src/app/ext/`)
- **AI Agents**: Multi-agent collaboration using LangChain and LangGraph.
- **Custom Tools**: Domain-specific tools for agents to interact with the finance core.


## 🔧 Architecture and Patterns

### Modular Architecture

Each module follows a consistent structure:

```
module_name/
├── controller.py    # Endpoints and routes
├── services.py      # Business logic
├── models.py        # Database models
└── schemas.py       # Pydantic schemas (validation)
```

### Automatic Route Registration

Routes are automatically registered based on the folder structure:

```python
# core/utils/import_modules.py analyzes the modules/ folder
# and automatically registers all found routers
```

### Middleware Pipeline

1. **CORS Middleware**: Allowed origins configuration
2. **JWT Verify**: Token validation on protected routes
3. **Role Verify**: Role-based permission verification

### Database Connections

**Asynchronous** (recommended for endpoints):
```python
from core.database import get_async_db

@router.get("/")
async def endpoint(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

**Synchronous** (for initialization):
```python
from core.database.sync_connection import engineSync
BaseSync.metadata.create_all(engineSync)
```

### Event System (ChannelEvent)

The core of asynchronous communication is `ChannelEvent`, which allows:

1. **Subscribe/Listen**: `@channel.subscribe_to` and `@channel.listen_to` decorators.
2. **Dependency Injection**: Use of `result = channel.DependsEvent(event_result)` to receive results from previous events.
3. **Smart Injection**: Subscribers automatically receive the `result` argument if declared in their signature.
4. **Resilience**: Robust event initialization and error handling.

## 🔐 Security

### Implemented Best Practices

1. **Hashed Passwords**: Use of bcrypt for secure hashing
2. **JWT with Expiration**: Tokens with limited lifespan
3. **Configured CORS**: Control over allowed origins
4. **Input Validation**: Pydantic validates all input data
5. **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injections
6. **Environment Variables**: Sensitive credentials in .env files

### Generate Secure JWT Key

```python
import secrets
jwt_key = secrets.token_hex(32)
print(jwt_key)
```

## 📊 Database and Performance

### **Connection Optimization**
The project implements a high-performance database connection strategy:
- **Pool Warm-up**: On application startup, a `warm_up_async_db` task is executed to establish initial connections, preventing the overhead on the first user request.
- **Optimized Parameters**:
    - `pool_size=10` / `max_overflow=20`
    - `pool_pre_ping=True` (resilience against stale connections)
    - `pool_use_lifo=True` (improves cache hit ratio)
    - `pool_recycle=1800` (prevents DB-side connection timeouts)

### **Main Models**
- **Finance Core**: `Balance`, `Transaction`, `Invoice`, `BusinessEntity`, `Person`.
- **Identity & Access**: `User`, `Role`, `Permission`, `Menu`.
- **System**: `Options` (Dynamic configuration), `ApiToken`.

### **Migrations**
The project uses **Alembic** for schema versioning. Tables are automatically synchronized during the initial setup via the `Base.metadata.create_all` hook, but Alembic is recommended for production updates.


## 🎨 Administrative Panel

The administrative panel includes:

- **Dashboard**: System overview
- **User Management**: Full CRUD
- **Roles and Permissions Management**: Visual assignment
- **Menu Configuration**: Menu editor
- **Logs and Monitoring**: Log visualization

**Access**: `http://localhost:8000/admin`

## 📈 Monitoring and Metrics

### Prometheus

Metrics available at `/metrics`:

- Number of requests
- Response latency
- HTTP errors
- Resource usage

### Grafana Integration

```yaml
# Example configuration for Grafana
datasources:
  - name: Prometheus
    type: prometheus
    url: http://localhost:8000/metrics
```

## 🧪 Testing

### Test Structure (Recommended)

```
tests/
├── test_auth.py
├── test_users.py
├── test_roles.py
└── conftest.py
```

### Test Example

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

## 🌐 Deployment

### Production Environment Variables

```env
MODE=PRODUCTION
JWT_KEY=super_secure_production_key
DB_HOST=db.production.com
DB_PASSWORD=secure_password
```

### Nginx as Reverse Proxy

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

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

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the project
2. Create a branch for your feature (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## 📞 Support

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Socket.IO Documentation**: https://socket.io/docs/
- **Repository**: https://github.com/TheGuyInTheShell/fastapi-template

## 🎯 Upcoming Features

- [ ] SMTP Connection
- [ ] Per-user rate limiting
- [ ] Full Tests
- [ ] Multi-language support (i18n)

---

**Developed with ❤️ using FastAPI**
