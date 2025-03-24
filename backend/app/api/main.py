from fastapi import APIRouter

from app.api.routes import items, login, private, users, utils
from app.core.config import settings
from app.api.endpoints.main import api_router as endpoints_router

api_router = APIRouter()

api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(endpoints_router)
 
if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
    