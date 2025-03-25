from fastapi import APIRouter, UploadFile, File, HTTPException, Request, BackgroundTasks, Depends
from fastapi.responses import FileResponse
import os
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import List
import logging

from app.api.deps import get_api_key


# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 一時ファイルを保存するディレクトリ
TEMP_DIR = Path("./temp_uploads")
# ディレクトリが存在しない場合は作成
TEMP_DIR.mkdir(exist_ok=True)

# 最大ファイルサイズ（5MB）
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes

# MIMEタイプ初期化
mimetypes.init()

@router.post("/upload", response_model=dict, name="upload_file")
async def upload_file(file: UploadFile = File(...), request: Request = None, api_key: str = Depends(get_api_key)):
    """
    ファイルをアップロードし、サーバー側の一時領域に保存するエンドポイント
    
    - **file**: アップロードするファイル（必須）
    - **最大サイズ**: 5MB
    
    **戻り値**:
    - filename: アップロードされたファイル名
    - file_path: サーバー上の保存パス
    - file_size: ファイルサイズ（バイト）
    - content_type: ファイルのMIMEタイプ
    - file_url: ファイルへの直接アクセスURL
    """
    try:
        # ファイルが空でないか確認
        if not file.filename:
            raise HTTPException(status_code=400, detail="ファイルが選択されていません")
        
        # ファイルサイズチェック（ヘッダーから取得できる場合）
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"ファイルサイズが大きすぎます。最大サイズは5MBです。"
            )
        
        # 保存先ファイルパスを設定
        file_path = TEMP_DIR / file.filename
        
        # ファイルを保存（チャンクで読み込みながらサイズチェック）
        file_size = 0
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MBずつ読み込む
                file_size += len(chunk)
                
                # サイズ制限チェック
                if file_size > MAX_FILE_SIZE:
                    buffer.close()
                    # 不完全なファイルを削除
                    os.remove(file_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"ファイルサイズが大きすぎます。最大サイズは5MBです。"
                    )
                
                buffer.write(chunk)
        
        # ファイルの情報を取得
        absolute_path = str(file_path.absolute())
        
        # ファイルへのURLを動的に生成
        file_url = request.url_for("files_serve", filename=file.filename)
        
        logger.info(f"ファイルをアップロードしました: {file.filename}, サイズ: {file_size} bytes")
        
        return {
            "filename": file.filename,
            "file_path": absolute_path,
            "file_size": file_size,
            "content_type": file.content_type or guess_content_type(file.filename),
            "saved_successfully": True,
            "file_url": str(file_url)  # URLオブジェクトを文字列に変換
        }
            
    except HTTPException:
        # 既に処理されたHTTPExceptionはそのまま再送
        raise
    except Exception as e:
        logger.error(f"ファイルアップロード中にエラー: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"ファイル保存中にエラー: {str(e)}")

@router.get("/files", response_model=List[dict], name="list_files")
async def list_files(request: Request = None, api_key: str = Depends(get_api_key)):
    """
    一時領域に保存されているファイル一覧を取得するエンドポイント
    
    **戻り値**:
    - ファイル情報のリスト（filename, file_path, file_size, modified_time, content_type, file_url）
    """
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
                
                # 動的にファイルURLを生成
                file_url = request.url_for("files_serve", filename=file_path.name)
                
                files_info.append({
                    "filename": file_path.name,
                    "file_path": str(file_path.absolute()),
                    "file_size": stats.st_size,
                    "modified_time": modified_time.isoformat(),
                    "content_type": guess_content_type(file_path.name),
                    "file_url": str(file_url)
                })
        
        # ファイル名でソート
        return sorted(files_info, key=lambda x: x["filename"])
            
    except Exception as e:
        logger.error(f"ファイル一覧取得中にエラー: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"ファイル一覧取得中にエラー: {str(e)}")

@router.get("/file-info/{filename}", response_model=dict, name="get_file_info")
async def get_file_info(filename: str, request: Request = None, api_key: str = Depends(get_api_key)):
    """
    指定したファイル名のファイル情報を取得するエンドポイント
    
    - **filename**: 情報を取得するファイル名
    
    **戻り値**:
    - filename: ファイル名
    - file_path: サーバー上の保存パス
    - file_size: ファイルサイズ（バイト）
    - modified_time: 最終更新日時
    - content_type: ファイルのMIMEタイプ
    - file_url: ファイルへの直接アクセスURL
    - exists: ファイルの存在確認
    """
    try:
        # ファイルパスを構築
        file_path = TEMP_DIR / filename
        
        # ファイルが存在するか確認
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(
                status_code=404, 
                detail=f"ファイル '{filename}' が見つかりません"
            )
        
        # ファイルの情報を取得
        stats = file_path.stat()
        modified_time = datetime.fromtimestamp(stats.st_mtime)
        
        # 動的にファイルURLを生成
        file_url = request.url_for("files_serve", filename=filename)
        
        return {
            "filename": filename,
            "file_path": str(file_path.absolute()),
            "file_size": stats.st_size,
            "modified_time": modified_time.isoformat(),
            "content_type": guess_content_type(filename),
            "file_url": str(file_url),
            "exists": True
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ファイル情報取得中にエラー: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"ファイル情報の取得中にエラー: {str(e)}")

@router.get("/files/{filename}", name="files_serve")
async def files_serve(filename: str, api_key: str = Depends(get_api_key)):
    """
    指定したファイル名のファイルを直接提供するエンドポイント
    
    - **filename**: 提供するファイル名
    
    **戻り値**:
    - ファイルの内容（バイナリ）
    - 画像やPDFなどはブラウザで直接表示、その他はダウンロードダイアログ表示
    """
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
        
        # 表示可能なファイルタイプかどうかを判断
        is_displayable = content_type.startswith(('image/', 'application/pdf', 'text/'))
        content_disposition_type = "inline" if is_displayable else "attachment"
        
        logger.info(f"ファイル提供: {filename}, タイプ: {content_type}, 表示方法: {content_disposition_type}")
        
        # ファイルをレスポンスとして返す
        return FileResponse(
            path=file_path,
            media_type=content_type,
            filename=filename,
            content_disposition_type=content_disposition_type
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ファイル提供中にエラー: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"ファイル提供中にエラー: {str(e)}")

@router.delete("/files/{filename}", response_model=dict, name="delete_file")
async def delete_file(filename: str, api_key: str = Depends(get_api_key)):
    """
    指定したファイル名のファイルを削除するエンドポイント
    
    - **filename**: 削除するファイル名
    
    **戻り値**:
    - message: 処理結果メッセージ
    - filename: 削除したファイル名
    """
    try:
        # ファイルパスを構築
        file_path = TEMP_DIR / filename
        
        # ファイルが存在するか確認
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(
                status_code=404, 
                detail=f"ファイル '{filename}' が見つかりません"
            )
        
        # ファイルを削除
        os.remove(file_path)
        
        logger.info(f"ファイル削除: {filename}")
        
        return {
            "message": "ファイルを正常に削除しました",
            "filename": filename
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ファイル削除中にエラー: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"ファイル削除中にエラー: {str(e)}")

@router.post("/cleanup", response_model=dict, name="cleanup_files")
async def cleanup_files(background_tasks: BackgroundTasks, api_key: str = Depends(get_api_key)):
    """
    一時ファイル領域をクリーンアップするエンドポイント（古いファイルを削除）
    
    **戻り値**:
    - message: 処理結果メッセージ
    """
    try:
        # バックグラウンドタスクとしてクリーンアップを実行
        background_tasks.add_task(perform_cleanup)
        
        return {
            "message": "クリーンアップを開始しました。古いファイルがバックグラウンドで削除されます。"
        }
            
    except Exception as e:
        logger.error(f"クリーンアップ処理の開始中にエラー: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"クリーンアップ処理の開始中にエラー: {str(e)}")

async def perform_cleanup():
    """一時ファイルをクリーンアップする関数（古いファイルを削除）"""
    try:
        # 古いファイルを削除するロジックを実装
        # 例：24時間以上経過したファイルを削除
        now = datetime.now()
        file_count = 0
        
        for file_path in TEMP_DIR.iterdir():
            if file_path.is_file():
                # ファイルの最終更新時間を取得
                modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                # 24時間以上経過したファイルを削除
                if (now - modified_time).total_seconds() > 24 * 3600:
                    os.remove(file_path)
                    file_count += 1
        
        logger.info(f"クリーンアップ完了: {file_count}個のファイルを削除しました")
            
    except Exception as e:
        logger.error(f"クリーンアップ処理中にエラー: {str(e)}", exc_info=True)
        # バックグラウンドタスクなのでエラーを投げない
        # ログに記録するだけ

def guess_content_type(filename: str) -> str:
    """ファイル名の拡張子からコンテンツタイプを推測する"""
    # mimetypesモジュールを使用して自動検出
    content_type, _ = mimetypes.guess_type(filename)
    
    # 検出できなかった場合はデフォルト値を使用
    if content_type is None:
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
        content_type = content_types.get(extension, 'application/octet-stream')
    
    return content_type