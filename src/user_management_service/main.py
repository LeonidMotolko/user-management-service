from fastapi import FastAPI

from user_management_service.presentation.api.v1.users import (
    router as users_router,
)

app = FastAPI(title="User Management Service")

app.include_router(users_router, prefix="/api/v1")
