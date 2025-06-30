#!/usr/bin/env python3
"""
シンプルな呼吸解析APIサーバー
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ストレージディレクトリの作成
os.makedirs('data', exist_ok=True)
os.makedirs('data/analysis', exist_ok=True)

app = FastAPI(title="呼吸解析API", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# シンプルなAPIキー認証
API_KEY = os.getenv('API_KEY', 'test-key-123')

def verify_api_key(api_key: str = Depends(lambda x: x)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

class SimpleAnalyzer:
    def __init__(self):
        self.data_dir = 'data/analysis'
        os.makedirs(self.data_dir, exist_ok=True)
    
    def analyze_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        breathing_rates = data.get('breathing_rates', [])
        if not breathing_rates:
            raise ValueError("呼吸データが空です")
        
        result = {
            "id": str(uuid.uuid4()),
            "device_id": data.get('device_id', 'unknown'),
            "timestamp": datetime.now().isoformat(),
            "breathing_rate": sum(breathing_rates) / len(breathing_rates),
            "min_rate": min(breathing_rates),
            "max_rate": max(breathing_rates),
            "data_points": len(breathing_rates)
        }
        
        self.save_result(result)
        return result
    
    def save_result(self, result: Dict[str, Any]):
        file_path = os.path.join(self.data_dir, f"{result['id']}.json")
        with open(file_path, 'w') as f:
            json.dump(result, f, indent=2)
    
    def get_results(self, device_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        results = []
        files = [f for f in os.listdir(self.data_dir) if f.endswith('.json')]
        files.sort(reverse=True)
        
        for filename in files[:limit]:
            file_path = os.path.join(self.data_dir, filename)
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                if device_id is None or data.get('device_id') == device_id:
                    results.append(data)
            except Exception as e:
                logger.warning(f"ファイル読み込みエラー {filename}: {e}")
        
        return results

analyzer = SimpleAnalyzer()

@app.get("/")
async def root():
    return {"message": "呼吸解析API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/analyze")
async def analyze_breathing(
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key)
):
    try:
        result = analyzer.analyze_data(data)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/results")
async def get_results(
    device_id: Optional[str] = None,
    limit: int = 50,
    api_key: str = Depends(verify_api_key)
):
    try:
        results = analyzer.get_results(device_id=device_id, limit=limit)
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    
    logger.info(f"サーバーを起動: {host}:{port}")
    uvicorn.run(app, host=host, port=port) 