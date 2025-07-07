import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import UploadFile
from ipfs_manager import IPFSManager

logger = logging.getLogger(__name__)

class BreathingAnalysisService:
    """呼吸解析サービスクラス"""
    
    def __init__(self, ipfs_manager: Optional[IPFSManager] = None):
        """サービス初期化"""
        self.storage_dir = os.getenv('STORAGE_DIR', '/app/storage')
        self.analysis_dir = os.path.join(self.storage_dir, 'analysis')
        self.csi_data_dir = os.path.join(self.storage_dir, 'csi_data')
        self.ipfs_dir = os.path.join(self.storage_dir, 'ipfs')
        
        # ディレクトリの作成
        os.makedirs(self.analysis_dir, exist_ok=True)
        os.makedirs(self.csi_data_dir, exist_ok=True)
        os.makedirs(self.ipfs_dir, exist_ok=True)
        
        self.ipfs_manager = ipfs_manager
        
    async def process_analysis_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        呼吸解析データの処理
        
        Args:
            data: 呼吸解析リクエストデータ
            
        Returns:
            処理結果
        """
        try:
            logger.info(f"呼吸解析データの処理を開始: デバイスID {data.get('metadata', {}).get('device_id', 'unknown')}")
            
            # データの検証
            if not data.get('window_results'):
                raise ValueError("ウィンドウ結果が空です")
                
            # 統計情報の計算
            breathing_rates = [result['breathing_rate'] for result in data['window_results']]
            
            processed_data = {
                "id": str(uuid.uuid4()),
                "device_id": data['metadata']['device_id'],
                "window_results": data['window_results'],
                "summary": data['summary'],
                "metadata": data['metadata'],
                "statistics": {
                    "total_windows": len(data['window_results']),
                    "average_breathing_rate": sum(breathing_rates) / len(breathing_rates) if breathing_rates else None,
                    "min_breathing_rate": min(breathing_rates) if breathing_rates else None,
                    "max_breathing_rate": max(breathing_rates) if breathing_rates else None,
                    "std_breathing_rate": self._calculate_std(breathing_rates) if breathing_rates else None
                },
                "processed_at": datetime.now().isoformat()
            }
            
            logger.info(f"呼吸解析データの処理が完了: ID {processed_data['id']}")
            return processed_data
            
        except Exception as e:
            logger.error(f"呼吸解析データ処理中にエラーが発生: {e}")
            raise
            
    async def save_analysis_result(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析結果の保存
        
        Args:
            result_data: 解析結果データ
            
        Returns:
            保存された解析結果
        """
        try:
            # ファイルに保存
            file_path = os.path.join(self.analysis_dir, f"{result_data['id']}.json")
            
            with open(file_path, 'w') as f:
                json.dump(result_data, f, indent=2)
                
            logger.info(f"解析結果を保存しました: {file_path}")
            
            # IPFS連携（オプショナル）
            if self.ipfs_manager and self.ipfs_manager.connection_status:
                try:
                    ipfs_hash = await self.ipfs_manager.upload_file(file_path)
                    if ipfs_hash:
                        result_data['ipfs_hash'] = ipfs_hash
                        ipfs_info = {
                            'result_id': result_data['id'],
                            'ipfs_hash': ipfs_hash,
                            'timestamp': datetime.now().isoformat(),
                            'file_path': file_path
                        }
                        ipfs_file_path = os.path.join(self.ipfs_dir, f"{result_data['id']}_ipfs.json")
                        with open(ipfs_file_path, 'w') as f:
                            json.dump(ipfs_info, f, indent=2)
                        await self.ipfs_manager.pin_file(ipfs_hash)
                        logger.info(f"IPFS連携が完了しました: {ipfs_hash}")
                    else:
                        logger.warning("IPFSアップロードに失敗しました")
                except Exception as e:
                    logger.warning(f"IPFS連携中にエラーが発生しました: {e}")
            else:
                logger.info("IPFSノードが利用できないため、IPFS連携をスキップします")
            
            return result_data
            
        except Exception as e:
            logger.error(f"解析結果保存中にエラーが発生: {e}")
            raise
            
    async def get_analysis_result(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        解析結果の取得
        
        Args:
            analysis_id: 解析ID
            
        Returns:
            解析結果（見つからない場合はNone）
        """
        try:
            file_path = os.path.join(self.analysis_dir, f"{analysis_id}.json")
            
            if not os.path.exists(file_path):
                logger.warning(f"解析結果ファイルが見つかりません: {file_path}")
                return None
                
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            return data
            
        except Exception as e:
            logger.error(f"解析結果取得中にエラーが発生: {e}")
            return None
            
    async def list_analysis_results(
        self, 
        device_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        解析結果の一覧取得
        
        Args:
            device_id: デバイスID（フィルタ用）
            start_date: 開始日（フィルタ用）
            end_date: 終了日（フィルタ用）
            limit: 取得件数制限
            offset: オフセット
            
        Returns:
            解析結果一覧
        """
        try:
            results = []
            
            # ファイル一覧の取得
            files = [f for f in os.listdir(self.analysis_dir) if f.endswith('.json')]
            files.sort(reverse=True)  # 新しい順
            
            # フィルタリングとページネーション
            filtered_files = files[offset:offset + limit]
            
            for filename in filtered_files:
                file_path = os.path.join(self.analysis_dir, filename)
                
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        
                    # デバイスIDフィルタ
                    if device_id and data.get('device_id') != device_id:
                        continue
                        
                    # 日付フィルタ
                    if start_date or end_date:
                        processed_at = data.get('processed_at')
                        if processed_at:
                            processed_date = datetime.fromisoformat(processed_at).date()
                            
                            if start_date:
                                start_dt = datetime.fromisoformat(start_date).date()
                                if processed_date < start_dt:
                                    continue
                                    
                            if end_date:
                                end_dt = datetime.fromisoformat(end_date).date()
                                if processed_date > end_dt:
                                    continue
                    
                    results.append(data)
                    
                except Exception as e:
                    logger.warning(f"ファイル読み込みエラー {filename}: {e}")
                    continue
                    
            return results
            
        except Exception as e:
            logger.error(f"解析結果一覧取得中にエラーが発生: {e}")
            return []
            
    async def save_csi_file(self, file: UploadFile, metadata: Dict[str, Any]) -> str:
        """
        CSIファイルの保存
        
        Args:
            file: アップロードされたファイル
            metadata: メタデータ
            
        Returns:
            保存されたファイルパス
        """
        try:
            # ファイル名の生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"csi_{metadata.get('device_id', 'unknown')}_{timestamp}_{file.filename}"
            file_path = os.path.join(self.csi_data_dir, filename)
            
            # ファイルの保存
            with open(file_path, 'wb') as f:
                content = await file.read()
                f.write(content)
                
            logger.info(f"CSIファイルを保存しました: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"CSIファイル保存中にエラーが発生: {e}")
            raise
            
    async def process_baseline_data(self, file_path: str, metadata: Dict[str, Any]):
        """
        ベースラインデータの処理
        
        Args:
            file_path: ファイルパス
            metadata: メタデータ
        """
        try:
            logger.info(f"ベースラインデータの処理を開始: {file_path}")
            
            # ベースラインデータの処理（実際の実装ではCSIデータの解析を行う）
            # ここでは簡略化
            
            logger.info("ベースラインデータの処理が完了しました")
            
        except Exception as e:
            logger.error(f"ベースラインデータ処理中にエラーが発生: {e}")
            raise
            
    async def process_csi_data(self, file_path: str, metadata: Dict[str, Any]):
        """
        CSIデータの処理
        
        Args:
            file_path: ファイルパス
            metadata: メタデータ
        """
        try:
            logger.info(f"CSIデータの処理を開始: {file_path}")
            
            # CSIデータの処理（実際の実装ではCSIデータの解析を行う）
            # ここでは簡略化
            
            logger.info("CSIデータの処理が完了しました")
            
        except Exception as e:
            logger.error(f"CSIデータ処理中にエラーが発生: {e}")
            raise
            
    def _calculate_std(self, values: List[float]) -> float:
        """
        標準偏差の計算
        
        Args:
            values: 値のリスト
            
        Returns:
            標準偏差
        """
        if not values:
            return 0.0
            
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5 