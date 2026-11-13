from fastapi import APIRouter

from app.api.v1.endpoints import auth, projects, tasks, users, workspaces
from app.schemas.error import COMMON_ERROR_RESPONSES

api_router = APIRouter(responses=COMMON_ERROR_RESPONSES)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(workspaces.router)
api_router.include_router(projects.router)
api_router.include_router(tasks.router)
