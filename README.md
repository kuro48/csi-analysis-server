# 呼吸解析API（IPFSノード機能付き・Docker対応）

CSIデータの解析とIPFS（InterPlanetary File System）への保存を行うAPIサーバーです。Dockerコンテナとして動作します。

## 特徴

- **CSIデータ処理**: エッジデバイスからのPCAPファイルを受信・保存
- **IPFS統合**: 収集したデータをIPFSに自動保存
- **呼吸解析**: 呼吸データの解析と結果保存
- **分散ストレージ**: IPFSによる分散化されたデータ保存
- **API認証**: APIキーによる認証機能
- **Docker対応**: コンテナ化された環境で簡単にデプロイ

## セットアップ

### 前提条件

- Docker
- Docker Compose

### 1. リポジトリのクローン
```bash
git clone <repository-url>
cd csi-analysis-server
```

### 2. Dockerコンテナのビルドと起動
```bash
# 起動スクリプトを使用（推奨）
./start.sh

# または直接Docker Composeで起動
docker-compose up -d
```

### 3. ログの確認
```bash
# 解析サーバーのログ
docker-compose logs -f csi-analysis-server
```

## 使用方法

### 1. ヘルスチェック
```bash
curl http://localhost:8000/health
```

### 2. IPFSノードの状態確認
```bash
curl http://localhost:8000/ipfs/status
```

### 3. CSIデータのアップロード（エッジデバイスから自動実行）
```bash
curl -X POST "http://localhost:8000/breathing-analysis/upload-csi" \
  -H "X-API-Key: test-key-123" \
  -F "file=@csi_data.pcap" \
  -F "metadata={\"device_id\":\"raspberry_pi_001\",\"type\":\"csi_measurement\",\"timestamp\":1640995200}"
```

### 4. 呼吸データの解析
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-123" \
  -d '{
    "device_id": "device001",
    "breathing_rates": [12, 13, 14, 12, 15, 13, 14, 12]
  }'
```

### 5. 結果の取得
```bash
# 全結果を取得
curl "http://localhost:8000/results?api_key=test-key-123"

# 特定デバイスの結果を取得
curl "http://localhost:8000/results?device_id=device001&api_key=test-key-123"
```

### 6. IPFSファイル一覧の取得
```bash
curl "http://localhost:8000/ipfs/files?api_key=test-key-123"
```

### 7. IPFSファイル情報の取得
```bash
curl "http://localhost:8000/ipfs/file/QmHash?api_key=test-key-123"
```

## Docker構成

### サービス構成

#### csi-analysis-server
- **ポート**: 8000 (API), 5001 (IPFS API), 8080 (IPFS Gateway)
- **機能**: 解析サーバー + 内蔵IPFSノード
- **ボリューム**: 
  - `./data` → `/app/data` (データ永続化)
  - `./logs` → `/app/logs` (ログ永続化)
  - `ipfs_data` → `/root/.ipfs` (IPFSデータ)

### 環境変数

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `HOST` | `0.0.0.0` | サーバーのホスト |
| `PORT` | `8000` | サーバーのポート |
| `API_KEY` | `test-key-123` | API認証キー |
| `IPFS_HOST` | `localhost` | IPFSノードのホスト |
| `IPFS_PORT` | `5001` | IPFSノードのポート |
| `IPFS_PROTOCOL` | `http` | IPFSプロトコル |

## データフロー

### CSIデータの処理
1. **受信**: エッジデバイスからPCAPファイルを受信
2. **保存**: ローカルストレージに保存
3. **IPFSアップロード**: IPFSノードに自動アップロード
4. **ピン留め**: データの永続化
5. **メタデータ保存**: IPFSハッシュとメタデータを記録

### 呼吸解析データの処理
1. **解析**: 呼吸データの統計処理
2. **保存**: 解析結果をローカルに保存
3. **IPFSアップロード**: 結果をIPFSに保存
4. **ハッシュ記録**: IPFSハッシュを結果に含める

## ディレクトリ構造

```
csi-analysis-server/
├── app.py                 # メインアプリケーション
├── requirements.txt       # 依存関係
├── Dockerfile            # Dockerイメージ定義
├── docker-compose.yml    # Docker Compose設定
├── .dockerignore         # Docker除外ファイル
├── start.sh              # 起動スクリプト
├── README.md             # ドキュメント
├── data/                 # データ保存ディレクトリ（ボリュームマウント）
│   ├── analysis/         # 解析結果
│   ├── csi/             # CSIデータ
│   └── ipfs/            # IPFS関連情報
└── logs/                # ログファイル（ボリュームマウント）
```

## 運用コマンド

### コンテナ管理
```bash
# 起動
docker-compose up -d

# 停止
docker-compose down

# 再起動
docker-compose restart

# ログ確認
docker-compose logs -f

# コンテナ内でコマンド実行
docker-compose exec csi-analysis-server bash
```

### データ管理
```bash
# データバックアップ
docker-compose exec csi-analysis-server tar -czf /app/data_backup.tar.gz /app/data

# IPFSデータの確認
docker-compose exec csi-analysis-server ipfs repo stat

# IPFSガベージコレクション
docker-compose exec csi-analysis-server ipfs repo gc
```

## トラブルシューティング

### コンテナ起動エラー
```bash
# ログの詳細確認
docker-compose logs csi-analysis-server

# コンテナの状態確認
docker-compose ps

# イメージの再ビルド
docker-compose build --no-cache
```

### IPFS接続エラー
```bash
# IPFSノードの状態確認
docker-compose exec csi-analysis-server ipfs id

# IPFS設定の確認
docker-compose exec csi-analysis-server ipfs config show
```

### ファイルアップロードエラー
- ボリュームマウントの確認
- ディスク容量の確認
- 権限の確認

### 認証エラー
- APIキーが正しく設定されているか確認
- リクエストヘッダーに`X-API-Key`が含まれているか確認

## セキュリティ

- APIキーによる認証
- CORS設定によるアクセス制御
- ファイルアップロードの検証
- IPFSノードの適切な設定
- コンテナの分離

## 開発環境

### ローカル開発
```bash
# 依存関係のインストール
pip install -r requirements.txt

# サーバーの起動
python app.py
```

### テスト
```bash
# コンテナのテスト
docker-compose up --abort-on-container-exit

# ヘルスチェック
curl http://localhost:8000/health
```

## ライセンス

このプロジェクトは研究目的で開発されています。 