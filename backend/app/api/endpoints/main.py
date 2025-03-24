# backend/app/api/endpoints/main.py
from fastapi import APIRouter
api_router = APIRouter()

# Each endpoints definition
from app.api.endpoints.hello import router as hello_router
api_router.include_router(hello_router, prefix="/hello", tags=["hello"])


from app.api.endpoints.ffmpeg import router as ffmpeg_router
api_router.include_router(ffmpeg_router, prefix="/ffmpeg", tags=["ffmpeg"])



# from app.api.endpoints.{endpoint_name} import router as {endpoint_name}_router
# api_router.include_router({endpoint_name}_router, prefix="/{endpoint_name}", tags=["{endpoint_name}"])
