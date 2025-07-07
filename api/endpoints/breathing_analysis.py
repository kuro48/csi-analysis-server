from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import json
import logging
from datetime import datetime
import os
import tempfile
import shutil

from ..models.breathing_analysis import (
    BreathingAnalysisRequest,
    BreathingAnalysisResponse,
    CSIUploadResponse,
    BreathingAnalysisResult
)
from ..middleware.auth import verify_api_key
from analysis.breathing_analysis import BreathingAnalysisService
from analysis.csi_processor import CSIProcessor
from ipfs_manager import IPFSManager

router = APIRouter(prefix="/breathing-analysis", tags=["breathing-analysis"])
logger = logging.getLogger(__name__)

# サービスインスタンスの初期化
ipfs_manager = IPFSManager()
analysis_service = BreathingAnalysisService(ipfs_manager=ipfs_manager)
csi_processor = None  # 設定読み込み後に初期化

def get_csi_processor():
    """CSIプロセッサーの取得"""
    global csi_processor
    if csi_processor is None:
        # 設定の読み込み（実際の実装では適切な設定管理が必要）
        config = {
            'storage': {
                'base_dir': '/app/data',
                'analysis_dir': '/app/data/analysis',
                'baseline_dir': '/app/data/baseline'
            }
        }
        csi_processor = CSIProcessor(config)
    return csi_processor

@router.post("/analyze", response_model=BreathingAnalysisResponse)
async def analyze_breathing(
    request: BreathingAnalysisRequest,
    api_key: str = Depends(verify_api_key)
) -> BreathingAnalysisResponse:
    """
    呼吸解析の実行
    
    Args:
        request: 解析リクエスト
        api_key: APIキー
        
    Returns:
        解析結果
    """
    try:
        logger.info(f"呼吸解析リクエストを受信: {request.device_id}")
        
        # 解析の実行
        result = await analysis_service.analyze_breathing(request)
        
        if result.breathing_rate is not None:
            logger.info(f"呼吸解析が完了: {result.breathing_rate} bpm")
        else:
            logger.info("呼吸解析が完了: 呼吸数を検出できませんでした")
        return result
        
    except Exception as e:
        logger.error(f"呼吸解析中にエラーが発生: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-csi", response_model=CSIUploadResponse)
async def upload_csi_file(
    file: UploadFile = File(...),
    metadata: str = Form(...),
    api_key: str = Depends(verify_api_key)
) -> CSIUploadResponse:
    """
    CSIファイル（PCAP）のアップロードと処理
    
    Args:
        file: アップロードされたPCAPファイル
        metadata: メタデータ（JSON文字列）
        api_key: APIキー
        
    Returns:
        アップロード結果
    """
    try:
        logger.info(f"CSIファイルのアップロードを受信: {file.filename}")
        
        # メタデータの解析
        try:
            metadata_dict = json.loads(metadata)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid metadata JSON: {e}")
        
        # ファイル形式の確認
        if not file.filename.endswith('.pcap'):
            raise HTTPException(status_code=400, detail="Only PCAP files are supported")
        
        # 一時ファイルとして保存
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pcap') as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name
        
        try:
            # CSIプロセッサーの取得
            processor = get_csi_processor()
            
            # CSIファイルの処理
            result = processor.process_csi_file(temp_file_path, metadata_dict)
            
            # 解析結果の保存
            analysis_dir = os.path.join('/app/data', 'analysis')
            result_file_path = processor.save_analysis_result(result, analysis_dir)
            
            # データベースに保存
            analysis_result = BreathingAnalysisResult(
                device_id=result['device_id'],
                timestamp=result['timestamp'],
                breathing_rate=result['breathing_rate'],
                peak_frequency=result['peak_frequency'],
                peak_height=result['peak_height'],
                selected_subcarriers=result['selected_subcarriers'],
                location=result['location'],
                collection_duration=result['collection_duration'],
                channel_width=result['channel_width'],
                result_file_path=result_file_path,
                processed_at=result['processed_at']
            )
            
            await analysis_service.save_analysis_result(analysis_result)
            
            if result['breathing_rate'] is not None:
                logger.info(f"CSIファイルの処理が完了: {result['breathing_rate']} bpm")
            else:
                logger.info("CSIファイルの処理が完了: 呼吸数を検出できませんでした")
            
            return CSIUploadResponse(
                success=True,
                message="CSI file processed successfully",
                analysis_id=analysis_result.id,
                breathing_rate=result['breathing_rate'],
                timestamp=result['timestamp']
            )
            
        finally:
            # 一時ファイルの削除
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSIファイル処理中にエラーが発生: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/{device_id}", response_model=Dict[str, Any])
async def get_analysis_results(
    device_id: str,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    limit: int = 100,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    解析結果の取得
    
    Args:
        device_id: デバイスID
        start_time: 開始時刻（UNIXタイムスタンプ）
        end_time: 終了時刻（UNIXタイムスタンプ）
        limit: 取得件数制限
        api_key: APIキー
        
    Returns:
        解析結果のリスト
    """
    try:
        logger.info(f"解析結果取得リクエスト: {device_id}")
        
        results = await analysis_service.get_analysis_results(
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return {
            "device_id": device_id,
            "results": [result.dict() for result in results],
            "count": len(results),
            "retrieved_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"解析結果取得中にエラーが発生: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/{device_id}/latest", response_model=BreathingAnalysisResult)
async def get_latest_analysis_result(
    device_id: str,
    api_key: str = Depends(verify_api_key)
) -> BreathingAnalysisResult:
    """
    最新の解析結果の取得
    
    Args:
        device_id: デバイスID
        api_key: APIキー
        
    Returns:
        最新の解析結果
    """
    try:
        logger.info(f"最新解析結果取得リクエスト: {device_id}")
        
        result = await analysis_service.get_latest_analysis_result(device_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="No analysis results found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"最新解析結果取得中にエラーが発生: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    ヘルスチェック
    
    Returns:
        システムの状態
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "breathing-analysis-api"
    } 