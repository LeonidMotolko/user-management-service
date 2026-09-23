import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from user_management_service.config import settings
from user_management_service.core.logging import setup_logging
from user_management_service.domain.exceptions import (
    DomainError,
    GroupNotFoundError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from user_management_service.infrastructure.messaging.connection import (
    close_rabbitmq_connection,
)
from user_management_service.presentation.api.v1.auth import (
    router as auth_router,
)
from user_management_service.presentation.api.v1.user import (
    router as user_router,
)
from user_management_service.presentation.api.v1.users import (
    router as users_router,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    setup_logging(debug=settings.DEBUG)
    logger.info("Starting User Management Service")
    yield
    await close_rabbitmq_connection()
    logger.info("Shutdown complete")


app = FastAPI(
    title="User Management Service",
    description="Production-grade user management microservice with Clean Architecture",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(users_router)


@app.get("/healthcheck", tags=["Health"], status_code=200)
async def healthcheck() -> Response:
    return Response(status_code=200)


@app.exception_handler(UserNotFoundError)
@app.exception_handler(GroupNotFoundError)
async def not_found_handler(request: Request, exc: DomainError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(UserAlreadyExistsError)
async def conflict_handler(request: Request, exc: DomainError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
