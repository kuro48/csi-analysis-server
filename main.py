#!/usr/bin/env python3
"""
PC1アプリケーションサーバーメインアプリケーション
呼吸解析データを受け取り、処理するAPIサーバー
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from api.endpoints import breathing_analysis
from analysis.breathing_analysis import BreathingAnalysisService

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ログディレクトリの作成
os.makedirs('logs', exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時の処理
    logger.info("アプリケーションサーバーを起動中...")
    
    # ストレージディレクトリの作成
    storage_dirs = [
        'storage',
        'storage/analysis',
        'storage/csi_data',
        'storage/temp'
    ]
    
    for directory in storage_dirs:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"ディレクトリを作成しました: {directory}")
    
    # サービスの初期化
    app.state.breathing_service = BreathingAnalysisService()
    
    logger.info("アプリケーションサーバーの起動が完了しました")
    
    yield
    
    # 終了時の処理
    logger.info("アプリケーションサーバーを終了中...")

# FastAPIアプリケーションの作成
app = FastAPI(
    title="呼吸解析APIサーバー",
    description="CSIデータを使用した呼吸解析システムのAPIサーバー",
    version="1.0.0",
    lifespan=lifespan
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの登録
app.include_router(breathing_analysis.router)

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "呼吸解析APIサーバー",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    try:
        # 基本的なシステム状態の確認
        status = {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "version": "1.0.0",
            "services": {
                "breathing_analysis": "running",
                "storage": "available"
            }
        }
        
        return JSONResponse(status_code=200, content=status)
        
    except Exception as e:
        logger.error(f"ヘルスチェック中にエラーが発生: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """グローバル例外ハンドラー"""
    logger.error(f"未処理の例外が発生しました: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "内部サーバーエラー",
            "message": str(exc),
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )

def main():
    """メイン関数"""
    # 設定の読み込み
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"サーバーを起動します: {host}:{port}")
    
    # uvicornサーバーの起動
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )

if __name__ == "__main__":
    main() 