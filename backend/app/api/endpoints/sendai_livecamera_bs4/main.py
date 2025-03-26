from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
from datetime import datetime
import re
from typing import Dict, Any, List

# deps.pyから認証関連の依存関係をインポート
from app.api.deps import get_api_key

router = APIRouter()

def scrape_bridge_data(url: str) -> Dict[str, Any]:
    """
    指定されたURLから橋の情報と画像をスクレイプする関数
    """
    try:
        # ページのHTMLを取得（エンコーディングを明示的に指定）
        response = requests.get(url)
        response.encoding = 'shift_jis'  # ページのエンコーディングをShift-JISに設定
        
        # HTMLをパース
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # タイトル（橋の名前）を取得
        bridge_name = soup.find('td', class_='style1')
        bridge_name = bridge_name.text.strip() if bridge_name else "不明"
        
        # 撮影日時を取得
        date_info = soup.find('td', class_='style2')
        capture_date = "不明"
        if date_info:
            date_text = date_info.text.strip()
            date_match = re.search(r'撮影日時：(\d+/\d+ \d+:\d+)', date_text)
            if date_match:
                capture_date = date_match.group(1)
        
        # 位置情報を取得
        location_info = soup.find('div', class_='style3')
        location = location_info.text.strip() if location_info else "不明"
        
        # 画像タグを見つける
        img_tags = soup.find_all('img')
        
        # 画像URLをフィルタリング (拡張子がjpgとjpegのみ)
        image_data = []
        for img in img_tags:
            if img.get('src') and any(img['src'].lower().endswith(ext) for ext in ['.jpg', '.jpeg']):
                # sp.gifなどの小さな画像を除外
                if 'sp.gif' not in img['src'].lower():
                    # 相対URLを絶対URLに変換
                    img_url = urljoin(url, img['src'])
                    
                    # 画像データを取得
                    try:
                        img_response = requests.get(img_url)
                        img_response.raise_for_status()
                        
                        # 画像情報を追加
                        image_data.append({
                            "url": img_url,
                            "filename": os.path.basename(img_url),
                            "content_type": img_response.headers.get('Content-Type', 'image/jpeg'),
                            "size": len(img_response.content)
                        })
                    except Exception as e:
                        print(f"画像の取得中にエラーが発生しました: {img_url}, エラー: {e}")
        
        # 画像がない場合
        if not image_data:
            return {
                "success": False,
                "error": "画像が見つかりませんでした",
                "message": "URLを確認してください"
            }
        
        # 結果をまとめる
        result = {
            "success": True,
            "bridge_info": {
                "name": bridge_name,
                "capture_date": capture_date,
                "location": location,
                "source_url": url,
                "scrape_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "images": image_data
        }
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "スクレイピング中にエラーが発生しました"
        }

# APIキー認証を使用したエンドポイント
@router.get("/bridge")
def get_bridge_data(url: str, api_key: str = Depends(get_api_key)):
    """
    指定したURLから橋の情報と画像URLを取得するエンドポイント
    
    - **url**: スクレイピングするウェブページのURL
    """
    if not url:
        raise HTTPException(status_code=400, detail="URLパラメータが必要です")
    
    result = scrape_bridge_data(url)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result

# 特定の画像を取得するエンドポイント
@router.get("/image")
async def get_image(image_url: str, api_key: str = Depends(get_api_key)):
    """
    指定された画像URLから画像データを取得して返す
    
    - **image_url**: 画像のURL
    """
    if not image_url:
        raise HTTPException(status_code=400, detail="画像URLが指定されていません")
    
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        
        # Content-Typeを検出
        content_type = response.headers.get('Content-Type', 'image/jpeg')
        
        # 画像データを直接返す
        return Response(
            content=response.content,
            media_type=content_type,
            headers={"Content-Disposition": f"inline; filename={os.path.basename(image_url)}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"画像の取得中にエラーが発生しました: {str(e)}")