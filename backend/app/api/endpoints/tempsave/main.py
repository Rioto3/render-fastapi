from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
from pathlib import Path
from datetime import datetime
from typing import List

router = APIRouter()

# 一時ファイルを保存するディレクトリ
TEMP_DIR = Path("./temp_uploads")
# ディレクトリが存在しない場合は作成
TEMP_DIR.mkdir(exist_ok=True)

@router.post("/upload", response_model=dict)
async def upload_file(file: UploadFile = File(...)):
    """ファイルをアップロードし、サーバー側の一時領域に保存するエンドポイント"""
    try:
        # ファイルが空でないか確認
        if not file.filename:
            raise HTTPException(status_code=400, detail="ファイルが選択されていません")
        
        # 保存先ファイルパスを設定
        file_path = TEMP_DIR / file.filename
        
        # ファイルを保存
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 保存したファイルの情報を返す
        file_size = os.path.getsize(file_path)
        
        return {
            "filename": file.filename,
            "file_size": file_size,
            "saved_successfully": True
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ファイル保存中にエラー: {str(e)}")





@router.get("/download/{filename}")
async def download_file(filename: str):
    """指定したファイル名のファイルをダウンロードするエンドポイント"""
    try:
        # ファイルパスを構築
        file_path = TEMP_DIR / filename
        
        # ファイルが存在するか確認
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(
                status_code=404, 
                detail=f"ファイル '{filename}' が見つかりません"
            )
        
        # コンテンツタイプを取得
        content_type = guess_content_type(filename)
        
        # ファイルをレスポンスとして返す
        return FileResponse(
            path=file_path,
            filename=filename,  # ダウンロード時のファイル名
            media_type=content_type
        )
            
    except HTTPException:
        # HTTPExceptionはそのまま再送
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"ファイルのダウンロード中にエラー: {str(e)}"
        )






@router.get("/files", response_model=List[dict])
async def list_files():
    """一時領域に保存されているファイル一覧を取得するエンドポイント"""
    try:
        # ディレクトリが存在することを確認
        if not TEMP_DIR.exists():
            return []
        
        files_info = []
        
        # ディレクトリ内のすべてのファイルを取得
        for file_path in TEMP_DIR.iterdir():
            if file_path.is_file():  # ディレクトリではなくファイルのみを対象
                # ファイルの情報を取得
                stats = file_path.stat()
                # UTC時間からローカル時間に変換
                modified_time = datetime.fromtimestamp(stats.st_mtime)
                
                files_info.append({
                    "filename": file_path.name,
                    "file_size": stats.st_size,
                    "modified_time": modified_time.isoformat(),
                    "content_type": guess_content_type(file_path.name)
                })
        
        # ファイル名でソート
        return sorted(files_info, key=lambda x: x["filename"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ファイル一覧取得中にエラー: {str(e)}")

# コンテンツタイプを拡張子から推測する簡易関数
def guess_content_type(filename: str) -> str:
    """ファイル名の拡張子からコンテンツタイプを推測する"""
    extension = os.path.splitext(filename)[1].lower()
    content_types = {
        '.txt': 'text/plain',
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.json': 'application/json',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.zip': 'application/zip',
        '.mp3': 'audio/mpeg',
        '.mp4': 'video/mp4',
    }
    return content_types.get(extension, 'application/octet-stream')  # デフォルトはバイナリデータ