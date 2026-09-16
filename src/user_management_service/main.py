import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from user_management_service.domain.exceptions import (
    DomainError,
    GroupNotFoundError,
    UserAlreadyExistsError,
    UserNotFoundError,
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

app = FastAPI(
    title="User Management Service",
    description="Production-grade user management microservice with Clean Architecture",
    version="0.1.0",
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")


@app.exception_handler(UserNotFoundError)
@app.exception_handler(GroupNotFoundError)
async def not_found_handler(request: Request, exc: DomainError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(UserAlreadyExistsError)
async def conflict_handler(request: Request, exc: DomainError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # TODO: убрать print() и завести нормальный logger после того, как найдём причину 500
    print("=" * 80)
    print(f"UNHANDLED EXCEPTION on {request.method} {request.url}")
    traceback.print_exc()
    print("=" * 80)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__, "message": str(exc)},
    )
