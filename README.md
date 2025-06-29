# CSI Analysis Server

CSI（Channel State Information）データの解析と呼吸率推定を行うFastAPIサーバーです。

## 概要

このサーバーは、エッジデバイスから送信されたPCAPファイルを受信し、CSIデータを解析して呼吸率を推定します。

## 機能

- **CSIデータ受信**: エッジデバイスからのPCAPファイル受信
- **データ解析**: PCAPファイルからCSIデータを抽出し、FFT解析を実行
- **呼吸率推定**: CSIデータから呼吸率を計算
- **RESTful API**: 解析結果の取得と管理用API
- **認証**: APIキーによる認証機能

## セットアップ

### 必要条件

- Python 3.8以上
- FastAPI
- データ解析ライブラリ（numpy, pandas, scipy, scikit-learn）

### インストール

```bash
# 依存関係のインストール
pip install -r requirements.txt

# サーバーの起動
python main.py
```

### 環境変数

```bash
export HOST=0.0.0.0
export PORT=8000
export DEBUG=true
```

## API エンドポイント

### CSIファイルアップロード
```
POST /breathing-analysis/upload-csi
Content-Type: multipart/form-data

Parameters:
- file: PCAPファイル
- metadata: JSON文字列（メタデータ）
- api_key: APIキー
```

### 解析結果取得
```
GET /breathing-analysis/results/{device_id}
GET /breathing-analysis/results/{device_id}/latest
```

### ヘルスチェック
```
GET /breathing-analysis/health
```

## アーキテクチャ

```
CSI Analysis Server
├── main.py                 # FastAPIアプリケーション
├── analysis/
│   ├── breathing_analysis.py  # 呼吸解析サービス
│   └── csi_processor.py       # CSIデータ処理
├── api/
│   ├── endpoints/             # APIエンドポイント
│   ├── models/                # データモデル
│   └── middleware/            # 認証ミドルウェア
└── requirements.txt           # 依存関係
```

## データ処理フロー

1. **PCAP受信**: エッジデバイスからPCAPファイルを受信
2. **CSI抽出**: PCAPファイルからCSIデータとタイムスタンプを抽出
3. **前処理**: 不要なサブキャリアを削除し、データを正規化
4. **FFT解析**: フーリエ変換を適用して周波数領域に変換
5. **呼吸率推定**: 呼吸周波数帯域でピークを検出し、呼吸率を計算
6. **結果保存**: 解析結果をデータベースに保存

## 設定

### API認証

`api/middleware/auth.py`でAPIキーを設定：

```python
VALID_API_KEYS = {
    "raspberry_pi_001": "your_api_key_here",
    "raspberry_pi_002": "another_api_key_here"
}
```

### 解析パラメータ

`analysis/csi_processor.py`のConfigクラスで解析パラメータを調整：

```python
class Config:
    BREATHING_MIN_FREQ = 0.2    # 呼吸周波数下限（Hz）
    BREATHING_MAX_FREQ = 0.33   # 呼吸周波数上限（Hz）
    TOP_SUBCARRIERS = 5         # 使用するサブキャリア数
```

## 使用方法

### サーバー起動

```bash
# 開発モード
python main.py

# 本番モード
uvicorn main:app --host 0.0.0.0 --port 8000
```

### テスト

```bash
# ヘルスチェック
curl http://localhost:8000/breathing-analysis/health

# 解析結果取得
curl -H "X-API-Key: your_api_key" \
     http://localhost:8000/breathing-analysis/results/raspberry_pi_001/latest
```

## トラブルシューティング

### よくある問題

- **ファイルアップロードエラー**: ディスク容量と権限の確認
- **解析エラー**: 依存関係のインストール確認
- **API認証エラー**: APIキーの設定確認

### ログ確認

```bash
tail -f logs/app_server_*.log
```

## ライセンス

このプロジェクトは研究目的で開発されています。 