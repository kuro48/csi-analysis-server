import os
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scapy.all import rdpcap, Raw
from scipy.signal import butter, filtfilt, find_peaks
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
import logging
import json
import time

logger = logging.getLogger(__name__)

class Config:
    """設定クラス"""
    BREATHING_MIN_FREQ = 0.2
    BREATHING_MAX_FREQ = 0.33
    TOP_SUBCARRIERS = 5

    CHANNEL_CONFIGS = {
        '20MHz': {
            'guard_bands': [(-32, -26), (27, 32)],
            'pilots': [-21, -7, 7, 21]
        },
        '80MHz': {
            'guard_bands': [
                (-122, -117), (-107, -102), (-92, -87), (-77, -72),
                (-62, -57), (-47, -42), (-32, -27), (-17, -12),
                (-2, 3), (12, 17), (27, 32), (42, 47),
                (57, 62), (72, 77), (87, 92), (102, 107),
                (117, 122)
            ],
            'pilots': [
                -103, -75, -39, -11, -89, -61, -25, 3,
                -53, -17, 19, 55, 33, 69, 105, 119
            ]
        }
    }

class CSIProcessor:
    """CSIデータ処理クラス（サーバー側）"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        CSIプロセッサーの初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config
        self._setup_matplotlib()
        
    def _setup_matplotlib(self):
        """matplotlibの設定"""
        plt.style.use('default')
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['legend.fontsize'] = 10
        plt.rcParams['figure.titlesize'] = 16
        plt.rcParams['axes.grid'] = True
        plt.rcParams['grid.alpha'] = 0.3
        plt.rcParams['figure.figsize'] = (12, 4)
        plt.rcParams['figure.dpi'] = 300

    def extract_csi_from_pcap(self, pcap_file_path: str) -> Tuple[List[float], List[Dict[str, Any]]]:
        """
        PCAPファイルからCSIデータとタイムスタンプを抽出
        
        Args:
            pcap_file_path: PCAPファイルのパス
            
        Returns:
            (タイムスタンプリスト, CSIデータリスト)
        """
        try:
            logger.info(f"PCAPファイルからCSIデータを抽出: {pcap_file_path}")
            
            packets = rdpcap(pcap_file_path)
            timestamps = []
            csi_data = []
            
            for packet in packets:
                if packet.haslayer('UDP'):
                    # タイムスタンプの抽出
                    timestamp = packet.time
                    timestamps.append(timestamp)
                    
                    # CSIデータの抽出（Rawレイヤーから）
                    if packet.haslayer(Raw):
                        raw_data = packet[Raw].load
                        # CSIデータの解析（実際の実装では適切なパース処理が必要）
                        csi_packet = self._parse_csi_packet(raw_data)
                        if csi_packet:
                            csi_data.append(csi_packet)
            
            logger.info(f"CSIデータ抽出完了: {len(timestamps)} パケット, {len(csi_data)} CSIデータ")
            return timestamps, csi_data
            
        except Exception as e:
            logger.error(f"PCAPファイルからのCSIデータ抽出中にエラーが発生: {e}")
            return [], []

    def _parse_csi_packet(self, raw_data: bytes) -> Optional[Dict[str, Any]]:
        """
        CSIパケットの解析（ダミー実装）
        実際の実装では、nexmonなどのCSIフォーマットに応じた適切なパース処理が必要
        
        Args:
            raw_data: 生データ
            
        Returns:
            解析されたCSIデータ
        """
        try:
            # ダミー実装：実際のCSIフォーマットに応じて実装が必要
            # ここでは簡略化のため、ダミーデータを返す
            if len(raw_data) < 10:
                return None
            
            # CSIデータの構造（例）
            # 実際の実装では、nexmonのCSIフォーマットに合わせて実装
            csi_data = {
                'timestamp': time.time(),
                'subcarriers': {}
            }
            
            # サブキャリアデータの生成（ダミー）
            for i in range(-64, 65):
                if i != 0:  # DCサブキャリアをスキップ
                    # 複素数のCSI値（振幅と位相）
                    amplitude = np.random.normal(1.0, 0.1)
                    phase = np.random.uniform(0, 2 * np.pi)
                    csi_data['subcarriers'][str(i)] = {
                        'amplitude': amplitude,
                        'phase': phase,
                        'real': amplitude * np.cos(phase),
                        'imag': amplitude * np.sin(phase)
                    }
            
            return csi_data
            
        except Exception as e:
            logger.error(f"CSIパケット解析中にエラーが発生: {e}")
            return None

    def convert_csi_to_dataframe(self, timestamps: List[float], csi_data: List[Dict[str, Any]]) -> Optional[pd.DataFrame]:
        """
        CSIデータをDataFrameに変換
        
        Args:
            timestamps: タイムスタンプリスト
            csi_data: CSIデータリスト
            
        Returns:
            CSIデータのDataFrame
        """
        try:
            if not csi_data:
                logger.warning("CSIデータが空です")
                return None
            
            # DataFrameの構築
            df_data = []
            for i, (timestamp, csi_packet) in enumerate(zip(timestamps, csi_data)):
                row = {'timestamp': timestamp}
                
                # サブキャリアデータの追加
                for subcarrier, values in csi_packet['subcarriers'].items():
                    # 複素数として結合
                    complex_value = values['real'] + 1j * values['imag']
                    row[subcarrier] = complex_value
                
                df_data.append(row)
            
            df = pd.DataFrame(df_data)
            logger.info(f"CSIデータをDataFrameに変換: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"CSIデータのDataFrame変換中にエラーが発生: {e}")
            return None

    def remove_unnecessary_subcarriers(self, df: pd.DataFrame, channel_width: str = '80MHz') -> pd.DataFrame:
        """不要なサブキャリアを削除"""
        if channel_width not in Config.CHANNEL_CONFIGS:
            raise ValueError(f"Unsupported channel width: {channel_width}")
        
        config = Config.CHANNEL_CONFIGS[channel_width]
        
        for start, end in config['guard_bands']:
            guard_cols = [str(i) for i in range(start, end + 1) if str(i) in df.columns]
            if guard_cols:
                df = df.drop(columns=guard_cols)
        
        pilot_cols = [str(i) for i in config['pilots'] if str(i) in df.columns]
        if pilot_cols:
            df = df.drop(columns=pilot_cols)
        
        return df

    def preprocess_csi_data(self, df: pd.DataFrame, channel_width: str = '80MHz') -> Optional[pd.DataFrame]:
        """CSIデータの前処理"""
        try:
            if df is None or df.empty:
                return None

            # 不要なサブキャリアの削除
            df = self.remove_unnecessary_subcarriers(df, channel_width)

            # 複素数データの振幅に変換
            subcarrier_cols = [col for col in df.columns if col != 'timestamp' and col.lstrip('-').isdigit()]
            for col in subcarrier_cols:
                if col in df.columns:
                    # 複素数から振幅を計算
                    df[col] = np.abs(df[col])

            return df

        except Exception as e:
            logger.error(f"Error preprocessing CSI data: {e}")
            return None

    def apply_fourier_transform(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """フーリエ変換の適用"""
        if df is None or df.empty:
            return None

        data_cols = [col for col in df.columns if col != 'timestamp' and col.lstrip('-').isdigit()]
        if not data_cols:
            return None

        all_fft_results = []
        for col in data_cols:
            signal = df[col].values
            if len(signal) < 2:
                continue

            N = len(signal)
            yf = np.fft.fft(signal)
            xf = np.fft.fftfreq(N, d=1.0/len(signal))
            
            positive_mask = xf > 0
            xf_positive = xf[positive_mask]
            yf_positive_abs = np.abs(yf[positive_mask])

            fft_df = pd.DataFrame({'frequency': xf_positive, col: yf_positive_abs})
            all_fft_results.append(fft_df.set_index('frequency'))

        if not all_fft_results:
            return None
        
        return pd.concat(all_fft_results, axis=1).reset_index()

    def compute_similarity_and_select_subcarriers(self, current_fft: pd.DataFrame, baseline_fft: pd.DataFrame) -> Tuple[List[str], Dict[str, float]]:
        """類似度計算とサブキャリア選択"""
        if current_fft is None or baseline_fft is None:
            return [], {}
        
        data_cols = [col for col in current_fft.columns if col != 'frequency']
        similarities = {}
        
        for col in data_cols:
            if col in baseline_fft.columns:
                similarity = cosine_similarity(
                    current_fft[col].values.reshape(1, -1),
                    baseline_fft[col].values.reshape(1, -1)
                )[0, 0]
                similarities[col] = similarity
        
        sorted_subcarriers = sorted(similarities.items(), key=lambda x: x[1])
        selected_cols = [col for col, _ in sorted_subcarriers[:Config.TOP_SUBCARRIERS]]
        
        return selected_cols, similarities

    def find_peak_spectrum(self, fft_df: pd.DataFrame, selected_cols: List[str]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """ピークスペクトルの検出"""
        if fft_df is None or not selected_cols:
            return None, None, None

        avg_spectrum = fft_df[selected_cols].mean(axis=1)
        breathing_mask = (fft_df['frequency'] >= Config.BREATHING_MIN_FREQ) & \
                        (fft_df['frequency'] <= Config.BREATHING_MAX_FREQ)

        breathing_range = avg_spectrum[breathing_mask]
        breathing_freqs = fft_df['frequency'][breathing_mask]
        
        if len(breathing_range) == 0:
            return None, None, None

        peaks, _ = find_peaks(breathing_range, prominence=0.1)
        
        if len(peaks) == 0:
            return None, None, None

        peak_freqs = breathing_freqs.iloc[peaks]
        peak_heights = breathing_range.iloc[peaks]
        dominant_peak_idx = peak_heights.argmax()
        peak_freq = peak_freqs.iloc[dominant_peak_idx]
        peak_height = peak_heights.iloc[dominant_peak_idx]
        breathing_rate = peak_freq * 60  # Convert Hz to bpm
        
        return peak_freq, peak_height, breathing_rate

    def process_csi_file(self, pcap_file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        CSIファイルの処理（完全版）
        
        Args:
            pcap_file_path: PCAPファイルのパス
            metadata: メタデータ
            
        Returns:
            処理結果
        """
        try:
            logger.info(f"CSIファイルの処理を開始: {pcap_file_path}")
            
            # PCAPファイルからCSIデータとタイムスタンプを抽出
            timestamps, csi_data = self.extract_csi_from_pcap(pcap_file_path)
            
            if not csi_data:
                raise ValueError("PCAPファイルからCSIデータを抽出できませんでした")
            
            # CSIデータをDataFrameに変換
            df = self.convert_csi_to_dataframe(timestamps, csi_data)
            if df is None or df.empty:
                raise ValueError("CSIデータのDataFrame変換に失敗しました")
            
            # CSIデータの前処理
            df = self.preprocess_csi_data(df, metadata.get('channel_width', '80MHz'))
            if df is None or df.empty:
                raise ValueError("CSIデータの前処理に失敗しました")
            
            # フーリエ変換
            fft_df = self.apply_fourier_transform(df)
            if fft_df is None or fft_df.empty:
                raise ValueError("フーリエ変換に失敗しました")
            
            # ベースラインFFTの読み込み（存在する場合）
            baseline_fft = None
            baseline_dir = os.path.join(self.config['storage']['base_dir'], 'baseline')
            if os.path.exists(baseline_dir):
                baseline_files = [f for f in os.listdir(baseline_dir) if f.endswith('.json')]
                if baseline_files:
                    # 最新のベースラインファイルを読み込み
                    latest_baseline = sorted(baseline_files)[-1]
                    with open(os.path.join(baseline_dir, latest_baseline), 'r') as f:
                        baseline_data = json.load(f)
                        if 'fft_data' in baseline_data:
                            baseline_fft = pd.DataFrame(baseline_data['fft_data'])
            
            # サブキャリアの選択
            selected_cols = []
            similarities = {}
            if baseline_fft is not None:
                selected_cols, similarities = self.compute_similarity_and_select_subcarriers(fft_df, baseline_fft)
            
            if not selected_cols:
                # ベースラインがない場合は、すべてのサブキャリアを使用
                selected_cols = [col for col in fft_df.columns if col != 'frequency']
            
            # 呼吸数の検出
            peak_freq, peak_height, breathing_rate = self.find_peak_spectrum(fft_df, selected_cols)
            
            # 結果の構築
            result = {
                'device_id': metadata.get('device_id', 'unknown'),
                'timestamp': metadata.get('timestamp', int(time.time())),
                'collection_duration': metadata.get('collection_duration', 60),
                'channel_width': metadata.get('channel_width', '80MHz'),
                'location': metadata.get('location', 'unknown'),
                'breathing_rate': float(breathing_rate) if breathing_rate is not None else 0.0,
                'peak_frequency': float(peak_freq) if peak_freq is not None else 0.0,
                'peak_height': float(peak_height) if peak_height is not None else 0.0,
                'selected_subcarriers': selected_cols,
                'similarities': similarities,
                'processed_at': datetime.now().isoformat(),
                'packet_count': len(timestamps),
                'csi_data_count': len(csi_data)
            }
            
            if breathing_rate is not None:
                logger.info(f"CSIファイルの処理が完了: 呼吸数 {breathing_rate:.1f} bpm")
            else:
                logger.info("CSIファイルの処理が完了: 呼吸数を検出できませんでした")
            return result
            
        except Exception as e:
            logger.error(f"CSIファイル処理中にエラーが発生: {e}")
            raise

    def save_analysis_result(self, result: Dict[str, Any], output_dir: str) -> str:
        """
        解析結果の保存
        
        Args:
            result: 解析結果
            output_dir: 出力ディレクトリ
            
        Returns:
            保存されたファイルパス
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"breathing_analysis_{timestamp}.json"
            file_path = os.path.join(output_dir, filename)
            
            with open(file_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            logger.info(f"解析結果を保存しました: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"解析結果保存中にエラーが発生: {e}")
            raise 