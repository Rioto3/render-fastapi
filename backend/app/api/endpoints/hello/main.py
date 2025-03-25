from fastapi import APIRouter, Depends

# deps.pyから認証関連の依存関係をインポート
from app.api.deps import get_api_key

router = APIRouter()

# APIキー認証を使用したエンドポイント
@router.get("/")
def hello_world(api_key: str = Depends(get_api_key)):
    return {"message": "Hello World"}

# APIキー認証を使用したエンドポイント（パスパラメータあり）
@router.get("/{name}")
def hello_name(name: str, api_key: str = Depends(get_api_key)):
    return {"message": f"こんにちは {name}さん"}