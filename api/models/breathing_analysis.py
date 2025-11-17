from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class WindowResult(BaseModel):
    """ウィンドウ解析結果モデル"""
    timestamp: str = Field(..., description="タイムスタンプ")
    breathing_rate: float = Field(..., description="呼吸数（bpm）")
    selected_subcarriers: List[str] = Field(..., description="選択されたサブキャリア")

class AnalysisSummary(BaseModel):
    """解析サマリーモデル"""
    total_windows: int = Field(..., description="総ウィンドウ数")
    average_breathing_rate: Optional[float] = Field(None, description="平均呼吸数")
    std_breathing_rate: Optional[float] = Field(None, description="呼吸数の標準偏差")
    min_breathing_rate: Optional[float] = Field(None, description="最小呼吸数")
    max_breathing_rate: Optional[float] = Field(None, description="最大呼吸数")

class Metadata(BaseModel):
    """メタデータモデル"""
    device_id: str = Field(..., description="デバイスID")
    analysis_timestamp: str = Field(..., description="解析タイムスタンプ")
    version: str = Field(..., description="バージョン")
    location: Optional[str] = Field(None, description="場所")
    channel_width: Optional[str] = Field(None, description="チャンネル幅")
    collection_duration: Optional[int] = Field(None, description="収集時間")

class BreathingAnalysisRequest(BaseModel):
    """呼吸解析リクエストモデル"""
    window_results: List[WindowResult] = Field(..., description="ウィンドウ解析結果")
    summary: AnalysisSummary = Field(..., description="解析サマリー")
    metadata: Metadata = Field(..., description="メタデータ")

class BreathingAnalysisResponse(BaseModel):
    """呼吸解析レスポンスモデル"""
    success: bool = Field(..., description="成功フラグ")
    message: str = Field(..., description="メッセージ")
    analysis_id: str = Field(..., description="解析ID")
    timestamp: str = Field(..., description="タイムスタンプ")

class BreathingAnalysisResult(BaseModel):
    """呼吸解析結果モデル（データベース用）"""
    id: Optional[str] = Field(None, description="解析ID")
    device_id: str = Field(..., description="デバイスID")
    timestamp: int = Field(..., description="タイムスタンプ")
    breathing_rate: float = Field(..., description="呼吸数（bpm）")
    peak_frequency: Optional[float] = Field(None, description="ピーク周波数")
    peak_height: Optional[float] = Field(None, description="ピーク高さ")
    selected_subcarriers: List[str] = Field(..., description="選択されたサブキャリア")
    location: Optional[str] = Field(None, description="場所")
    collection_duration: int = Field(..., description="収集時間")
    channel_width: str = Field(..., description="チャンネル幅")
    result_file_path: Optional[str] = Field(None, description="結果ファイルパス")
    processed_at: str = Field(..., description="処理日時")
    created_at: Optional[datetime] = Field(None, description="作成日時")
    updated_at: Optional[datetime] = Field(None, description="更新日時")
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "timestamp": self.timestamp,
            "breathing_rate": self.breathing_rate,
            "peak_frequency": self.peak_frequency,
            "peak_height": self.peak_height,
            "selected_subcarriers": self.selected_subcarriers,
            "location": self.location,
            "collection_duration": self.collection_duration,
            "channel_width": self.channel_width,
            "result_file_path": self.result_file_path,
            "processed_at": self.processed_at,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class CSIDataMetadata(BaseModel):
    """CSIデータメタデータモデル"""
    type: str = Field(..., description="データタイプ（baseline/measurement）")
    timestamp: Optional[int] = Field(None, description="タイムスタンプ")
    device_id: str = Field(..., description="デバイスID")
    collection_duration: Optional[int] = Field(None, description="収集時間")
    channel_width: Optional[str] = Field(None, description="チャンネル幅")
    location: Optional[str] = Field(None, description="場所")
    selected_subcarriers: Optional[List[str]] = Field(None, description="ハードウェアで選択されたサブキャリア")

class CSIDataFile(BaseModel):
    """CSIデータファイルモデル"""
    id: str = Field(..., description="ファイルID")
    filename: str = Field(..., description="ファイル名")
    file_path: str = Field(..., description="ファイルパス")
    metadata: CSIDataMetadata = Field(..., description="メタデータ")
    file_size: int = Field(..., description="ファイルサイズ")
    created_at: datetime = Field(..., description="作成日時")
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_path": self.file_path,
            "metadata": self.metadata.dict(),
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat()
        }

class CSIUploadResponse(BaseModel):
    """CSIファイルアップロードのレスポンスモデル"""
    success: bool = Field(..., description="成功フラグ")
    message: str = Field(..., description="メッセージ")
    analysis_id: Optional[str] = Field(None, description="解析ID")
    breathing_rate: Optional[float] = Field(None, description="呼吸数（bpm）")
    timestamp: Optional[str] = Field(None, description="タイムスタンプ") 