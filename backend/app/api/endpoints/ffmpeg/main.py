from fastapi import APIRouter, Response, Depends
import subprocess
import os
from app.api.deps import get_api_key

router = APIRouter()

@router.get("/capture_stream_screenshot", response_model=None)
async def capture_stream_screenshot(url: str, output_file: str, api_key: str = Depends(get_api_key)):
    result = run_ffmpeg(url, output_file)
    if os.path.exists(output_file):
        with open(output_file, "rb") as f:
            image_data = f.read()
        os.remove(output_file)
        return Response(content=image_data, media_type="image/jpeg")
    return {"message": f"処理結果: {result}"}


def run_ffmpeg(url, output_file):
    # FFmpegコマンドを作成
    command = [
        "ffmpeg",
        "-i", url,
        "-vframes", "1",  # 1フレームを取得
        "-q:v", "2",  # 品質設定
        output_file
    ]
    
    try:
        # コマンドを実行し、エラー出力も取得
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False
        )
        
        # 成功したかどうかをチェック
        if result.returncode == 0:
            return "画像取得成功"
        else:
            return f"エラー: {result.stderr}"
    except Exception as e:
        return f"例外発生: {str(e)}"