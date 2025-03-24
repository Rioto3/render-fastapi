from fastapi import FastAPI, HTTPException, APIRouter, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import subprocess
import os
import uuid

# FastAPIアプリケーションの作成
app = FastAPI()
router = APIRouter()

# スクリーンショットの保存ディレクトリ
SAVE_DIR = "screenshots"
os.makedirs(SAVE_DIR, exist_ok=True)

# `/images/` エンドポイントで `screenshots/` を公開
app.mount("/images", StaticFiles(directory=SAVE_DIR), name="images")

def run_ffmpeg(url: str, output_file: str):
    command = [
        "ffmpeg",
        "-y",  # 既存ファイルを強制的に上書き
        "-i", url,
        "-vframes", "1",
        "-q:v", "2",
        output_file
    ]
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("FFmpeg Output:", result.stdout)
        print("FFmpeg Error:", result.stderr)
    except subprocess.CalledProcessError as e:
        print("FFmpeg failed!")
        print("FFmpeg Output:", e.stdout)
        print("FFmpeg Error:", e.stderr)
        raise HTTPException(status_code=500, detail=f"FFmpeg execution failed: {e.stderr}")

@router.get("/screenshot")
async def create_screenshot(url: str = Query(..., description="URL of the video to capture"),
                            filename: str = Query(None, description="Output filename")):
    if not filename:
        filename = f"{uuid.uuid4()}.jpg"
    elif not filename.endswith(('.jpg', '.jpeg', '.png')):
        filename += '.jpg'

    output_path = os.path.join(SAVE_DIR, filename)

    try:
        run_ffmpeg(url, output_path)
        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="Failed to create screenshot")
        
        # アクセス可能なURLを返す
        return JSONResponse({"image_url": f"http://localhost:8000/images/{filename}"})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
