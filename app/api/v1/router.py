from fastapi import APIRouter

from app.api.v1.endpoints import auth, projects, tasks, users, workspaces
from app.schemas.error import ErrorResponse

api_router = APIRouter(
    responses={
        422: {"model": ErrorResponse, "description": "Request Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    }
)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(workspaces.router)
api_router.include_router(projects.router)
api_router.include_router(tasks.router)
