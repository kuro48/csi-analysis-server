#!/usr/bin/env python3
"""
統合呼吸解析APIサーバー（IPFSノード機能付き）
CSIデータを使用した呼吸解析システムの完全統合版
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from ipfs_manager import IPFSManager
from analysis.breathing_analysis import BreathingAnalysisService
from analysis.csi_processor import CSIProcessor
from api.endpoints import breathing_analysis

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/analysis_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ログディレクトリの作成
os.makedirs('logs', exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("統合呼吸解析サーバーを起動中...")
    storage_dirs = [
        'data', 'data/analysis', 'data/csi', 'data/ipfs',
        'storage', 'storage/analysis', 'storage/csi_data', 'storage/temp'
    ]
    for directory in storage_dirs:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"ディレクトリを作成しました: {directory}")
    app.state.breathing_service = BreathingAnalysisService()
    connected = await app.state.ipfs_manager.connect()
    if connected:
        logger.info(f"IPFSノード({app.state.ipfs_manager.ipfs_url})に接続しました。")
    else:
        logger.warning(f"IPFSノード({app.state.ipfs_manager.ipfs_url})への接続に失敗しました。")
    logger.info("統合呼吸解析サーバーの起動が完了しました")
    yield
    logger.info("統合呼吸解析サーバーを終了中...")

API_KEY = os.getenv('API_KEY', 'test-key-123')
IPFS_HOST = os.getenv('IPFS_HOST', 'ipfs-node')
IPFS_PORT = int(os.getenv('IPFS_PORT', 5001))
IPFS_PROTOCOL = os.getenv('IPFS_PROTOCOL', 'http')

app = FastAPI(
    title="統合呼吸解析APIサーバー（IPFSノード機能付き）", 
    description="CSIデータを使用した呼吸解析システムの完全統合版",
    version="2.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ipfs_manager = IPFSManager(host=IPFS_HOST, port=IPFS_PORT, protocol=IPFS_PROTOCOL)
csi_config = {
    'storage': {
        'base_dir': 'data',
        'analysis_dir': 'data/analysis',
        'baseline_dir': 'data/baseline'
    }
}
csi_processor = CSIProcessor(csi_config)

app.state.ipfs_manager = ipfs_manager
app.state.csi_processor = csi_processor

# APIルーティングはapi/endpoints/breathing_analysis.pyに集約
app.include_router(breathing_analysis.router)

@app.get("/")
async def root():
    return {
        "message": "呼吸解析API（IPFSノード機能付き）",
        "status": "running",
        "ipfs_connected": ipfs_manager.connection_status,
        "ipfs_url": ipfs_manager.ipfs_url
    }

@app.get("/health")
async def health():
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ipfs_connected": ipfs_manager.connection_status,
        "ipfs_url": ipfs_manager.ipfs_url
    }

if __name__ == "__main__":
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    logger.info(f"サーバーを起動: {host}:{port}")
    logger.info(f"IPFSノード設定: {ipfs_manager.ipfs_url}")
    uvicorn.run(app, host=host, port=port) 