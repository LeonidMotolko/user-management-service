# User Management Service

A production-grade **user management microservice** built with **FastAPI** and **Clean Architecture** principles. It provides authentication, authorization, user/group management, avatar storage, and password-reset notifications for other services in a distributed system.

## Features

- 🔐 **Authentication** — signup, login, JWT access/refresh tokens, password reset flow
- 👤 **User management** — retrieve, update, and delete the current user or (as an admin) any user
- 📄 **Paginated user listing** with role-based access control
- 🛡️ **Role-based authorization** — `USER`, `ADMIN`, `MODERATOR` roles plus group-based access rules
- 🖼️ **Avatar storage** via S3-compatible object storage
- 📨 **Async messaging** — password-reset events published to RabbitMQ for downstream processing (e.g. email delivery)
- 🗄️ **PostgreSQL** persistence via SQLAlchemy (async) with Alembic migrations
- ⚡ **Redis** for token blacklisting / caching
- 🧱 Clean Architecture: clear separation between domain, application, infrastructure, and presentation layers
- ✅ Test suite built with `pytest` / `pytest-asyncio`

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| Database | PostgreSQL (async, via `asyncpg` + SQLAlchemy) |
| Migrations | Alembic |
| Cache / token blacklist | Redis |
| Message broker | RabbitMQ (`aio-pika`) |
| Object storage | S3-compatible storage (`aioboto3`) |
| Auth | JWT (`PyJWT`) |
| Validation & settings | Pydantic / Pydantic Settings |
| Package management | [uv](https://github.com/astral-sh/uv) |
| Linting / formatting | Ruff, Ty |
| Testing | Pytest, pytest-asyncio |

## Architecture

The project follows **Clean Architecture**, organized into four layers under `src/user_management_service/`:

```
src/user_management_service/
├── domain/            # Entities, value objects, and domain exceptions
├── application/        # Use cases, DTOs, and repository/service interfaces
├── infrastructure/     # Concrete implementations: DB, cache, messaging, storage, security
└── presentation/       # FastAPI routers, dependencies, and request/response wiring
```

Dependencies always point inward — `presentation` depends on `application`, which depends on `domain`, while `infrastructure` implements the interfaces defined in `application`. This keeps business logic isolated from frameworks and external services.

## Prerequisites

- Python **3.13+**
- [uv](https://github.com/astral-sh/uv) for dependency and environment management
- Docker and Docker Compose (for running PostgreSQL, Redis, and RabbitMQ locally)

## Getting Started

### 1. Clone and configure environment variables

```bash
git clone <repository-url>
cd user-management-service
cp .env.example .env
```

Edit `.env` and set at least `SECRET_KEY`, along with any database, Redis, RabbitMQ, or AWS credentials relevant to your setup.

### 2. Start infrastructure services

```bash
docker compose up -d postgres redis rabbitmq
```

### 3. Install dependencies

```bash
make install-dev
```

### 4. Apply database migrations

```bash
uv run alembic upgrade head
```

### 5. Run the application

```bash
make run
```

The API will be available at `http://localhost:8000`, with interactive documentation at `http://localhost:8000/docs`.

### Running everything with Docker Compose

Alternatively, run the full stack (application included) in containers:

```bash
docker compose up --build
```

## Configuration

Configuration is managed via environment variables (see `.env.example`), loaded through Pydantic Settings:

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Secret key used to sign JWTs | *(required)* |
| `DEBUG` | Enable debug logging | `false` |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_HOST` / `POSTGRES_PORT` / `POSTGRES_DB` | PostgreSQL connection settings | `postgres` / `postgres` / `localhost` / `5433` / `user_db` |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` | Redis connection settings | `localhost` / `6379` / `0` |
| `RABBITMQ_HOST` / `RABBITMQ_PORT` / `RABBITMQ_USER` / `RABBITMQ_PASSWORD` | RabbitMQ connection settings | `localhost` / `5672` / `guest` / `guest` |
| `FRONTEND_RESET_PASSWORD_URL` | Frontend URL used in password-reset links | `http://localhost:3000/reset-password` |
| `AWS_REGION` / `AWS_S3_BUCKET` / `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_S3_ENDPOINT_URL` | S3-compatible storage settings for avatar uploads | — |

Additional settings such as `ACCESS_TOKEN_EXPIRE_MINUTES` and `REFRESH_TOKEN_EXPIRE_DAYS` can be found in `src/user_management_service/config.py`.

## API Overview

Interactive OpenAPI documentation is available at `/docs` once the service is running. Key endpoint groups:

### Auth (`/auth`)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/signup` | Register a new user |
| POST | `/auth/login` | Authenticate and receive access/refresh tokens |
| POST | `/auth/refresh-token` | Obtain a new access token from a refresh token |
| POST | `/auth/reset-password` | Request a password-reset email |

### User (`/user`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/user/me` | Get the current authenticated user |
| PATCH | `/user/me` | Update the current authenticated user |
| DELETE | `/user/me` | Delete the current authenticated user |
| GET | `/user/{user_id}` | Get a user by ID (admin or same-group only) |
| PATCH | `/user/{user_id}` | Update a user by ID (admin only) |
| DELETE | `/user/{user_id}` | Delete a user by ID (admin only) |

### Users (`/users`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/users` | List users with pagination |

### Health
| Method | Endpoint | Description |
|---|---|---|
| GET | `/healthcheck` | Service health check |

## Database Migrations

Migrations are managed with Alembic (`migrations/`). Common commands:

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "description"

# Apply all pending migrations
uv run alembic upgrade head

# Roll back the last migration
uv run alembic downgrade -1
```

## Testing

```bash
uv run pytest
```

The test suite (`tests/`) covers authentication, authorization, use cases, password reset, S3 storage, and health checks.

## Development

```bash
make install-dev   # Install dev dependencies
make lint          # Run Ruff and Ty static checks
make format        # Auto-format code with Ruff
make check          # Run all pre-commit hooks
```

Available `make` targets:

| Command | Description |
|---|---|
| `make install-dev` | Install development dependencies |
| `make lint` | Run Ruff and Ty |
| `make format` | Format code with Ruff |
| `make run` | Run the application |
| `make check` | Check the project with all pre-commit hooks |

## Project Structure

```
.
├── src/
│   ├── seed_db.py
│   └── user_management_service/
│       ├── application/        # Use cases, DTOs, interfaces
│       ├── core/                # Logging and cross-cutting utilities
│       ├── domain/              # Entities and domain exceptions
│       ├── infrastructure/      # DB, messaging, security, storage implementations
│       ├── presentation/        # API routers and dependencies
│       ├── config.py
│       └── main.py
├── migrations/                  # Alembic migration scripts
├── tests/                       # Test suite
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── pyproject.toml
└── .env.example
```
