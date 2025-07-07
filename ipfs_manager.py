import os
import logging
import ipfshttpclient
from typing import Dict, Any, Optional

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Docker分離運用を前提に、デフォルトhostは'ipfs-node'（docker-composeサービス名）
IPFS_HOST = os.getenv('IPFS_HOST', 'ipfs-node')
IPFS_PORT = int(os.getenv('IPFS_PORT', 5001))
IPFS_PROTOCOL = os.getenv('IPFS_PROTOCOL', 'http')

class IPFSManager:
    """IPFS管理クラス"""
    def __init__(self, host: str = IPFS_HOST, port: int = IPFS_PORT, protocol: str = IPFS_PROTOCOL):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.client = None
        self.ipfs_url = f"{protocol}://{host}:{port}/api/v0"
        self.connection_status = False

    async def connect(self) -> bool:
        try:
            self.client = ipfshttpclient.connect(self.ipfs_url)
            self.client.id()
            self.connection_status = True
            logger.info(f"IPFSノードに接続しました: {self.ipfs_url}")
            return True
        except Exception as e:
            logger.warning(f"IPFSノード({self.ipfs_url})への接続に失敗: {e}")
            self.connection_status = False
            return False

    async def upload_file(self, file_path: str) -> Optional[str]:
        if not self.connection_status:
            logger.warning(f"IPFSノード({self.ipfs_url})に接続されていません")
            return None
        try:
            result = self.client.add(file_path)
            ipfs_hash = result['Hash']
            logger.info(f"ファイルをIPFS({self.ipfs_url})にアップロードしました: {ipfs_hash}")
            return ipfs_hash
        except Exception as e:
            logger.error(f"IPFS({self.ipfs_url})アップロードエラー: {e}")
            return None

    async def get_file_info(self, ipfs_hash: str) -> Optional[Dict[str, Any]]:
        if not self.connection_status:
            logger.warning(f"IPFSノード({self.ipfs_url})に接続されていません")
            return None
        try:
            result = self.client.ls(ipfs_hash)
            return result
        except Exception as e:
            logger.error(f"IPFS({self.ipfs_url})ファイル情報取得エラー: {e}")
            return None

    async def pin_file(self, ipfs_hash: str) -> bool:
        if not self.connection_status:
            logger.warning(f"IPFSノード({self.ipfs_url})に接続されていません")
            return False
        try:
            self.client.pin.add(ipfs_hash)
            logger.info(f"ファイルをIPFS({self.ipfs_url})でピン留めしました: {ipfs_hash}")
            return True
        except Exception as e:
            logger.error(f"IPFS({self.ipfs_url})ピン留めエラー: {e}")
            return False 