# backend/app/api/endpoints/main.py
from fastapi import APIRouter
api_router = APIRouter()

# Each endpoints definition
from app.api.endpoints.hello import router as hello_router
api_router.include_router(hello_router, prefix="/hello", tags=["hello"])


from app.api.endpoints.ffmpeg import router as ffmpeg_router
api_router.include_router(ffmpeg_router, prefix="/ffmpeg", tags=["ffmpeg"])


from app.api.endpoints.tempsave import router as tempsave_router
api_router.include_router(tempsave_router, prefix="/tempsave", tags=["tempsave"])

# エンドポイントsendai_livecamera_bs4追加 20250326
from app.api.endpoints.sendai_livecamera_bs4 import router as sendai_livecamera_bs4_router
api_router.include_router(sendai_livecamera_bs4_router, prefix="/sendai_livecamera_bs4", tags=["sendai_livecamera_bs4"])
