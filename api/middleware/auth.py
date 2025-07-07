from fastapi import HTTPException, Depends, Header
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

# 有効なAPIキーのリスト（実際の実装ではデータベースから取得）
VALID_API_KEYS = {
    "raspberry_pi_001": "test-key-123",
    "raspberry_pi_002": "another_api_key_here"
}

async def verify_api_key(authorization: Optional[str] = Header(None)) -> str:
    """
    APIキーの検証
    
    Args:
        authorization: Authorizationヘッダー
        
    Returns:
        検証されたAPIキー
        
    Raises:
        HTTPException: 認証に失敗した場合
    """
    if not authorization:
        logger.warning("Authorizationヘッダーがありません")
        raise HTTPException(
            status_code=401,
            detail="Authorizationヘッダーが必要です",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Bearerトークンの形式をチェック
    if not authorization.startswith("Bearer "):
        logger.warning("無効なAuthorizationヘッダー形式")
        raise HTTPException(
            status_code=401,
            detail="無効なAuthorizationヘッダー形式です",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    api_key = authorization.replace("Bearer ", "")
    
    # APIキーの検証
    logger.info(f"受信したAPIキー: {api_key}")
    logger.info(f"有効なAPIキー: {list(VALID_API_KEYS.values())}")
    if api_key not in VALID_API_KEYS.values():
        logger.warning(f"無効なAPIキー: {api_key}")
        raise HTTPException(
            status_code=401,
            detail="無効なAPIキーです",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    logger.info("APIキーの検証が成功しました")
    return api_key

def get_device_id_from_api_key(api_key: str) -> Optional[str]:
    """
    APIキーからデバイスIDを取得
    
    Args:
        api_key: APIキー
        
    Returns:
        デバイスID（見つからない場合はNone）
    """
    for device_id, key in VALID_API_KEYS.items():
        if key == api_key:
            return device_id
    return None

class APIAuthMiddleware:
    """API認証ミドルウェアクラス"""
    
    def __init__(self):
        self.valid_api_keys = VALID_API_KEYS
        
    def add_api_key(self, device_id: str, api_key: str):
        """
        APIキーの追加
        
        Args:
            device_id: デバイスID
            api_key: APIキー
        """
        self.valid_api_keys[device_id] = api_key
        logger.info(f"APIキーを追加しました: {device_id}")
        
    def remove_api_key(self, device_id: str):
        """
        APIキーの削除
        
        Args:
            device_id: デバイスID
        """
        if device_id in self.valid_api_keys:
            del self.valid_api_keys[device_id]
            logger.info(f"APIキーを削除しました: {device_id}")
            
    def is_valid_api_key(self, api_key: str) -> bool:
        """
        APIキーの有効性チェック
        
        Args:
            api_key: APIキー
            
        Returns:
            有効フラグ
        """
        return api_key in self.valid_api_keys.values()
        
    def get_device_id(self, api_key: str) -> Optional[str]:
        """
        APIキーからデバイスIDを取得
        
        Args:
            api_key: APIキー
            
        Returns:
            デバイスID
        """
        return get_device_id_from_api_key(api_key) 