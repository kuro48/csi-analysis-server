# シンプル呼吸解析API

複雑なディレクトリ構造を排除し、1つのファイルで動作するシンプルな呼吸解析APIサーバーです。

## 特徴

- **単一ファイル**: `simple_app.py` 1つで全ての機能を提供
- **シンプルな構造**: 複雑なディレクトリ構造や抽象化レイヤーを排除
- **基本的な機能**: 呼吸データの解析、結果の保存・取得
- **軽量**: 最小限の依存関係

## セットアップ

```bash
# 依存関係のインストール
pip install -r simple_requirements.txt

# サーバーの起動
python simple_app.py
```

## 使用方法

### 1. ヘルスチェック
```bash
curl http://localhost:8000/health
```

### 2. 呼吸データの解析
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-123" \
  -d '{
    "device_id": "device001",
    "breathing_rates": [12, 13, 14, 12, 15, 13, 14, 12]
  }'
```

### 3. 結果の取得
```bash
# 全結果を取得
curl "http://localhost:8000/results?api_key=test-key-123"

# 特定デバイスの結果を取得
curl "http://localhost:8000/results?device_id=device001&api_key=test-key-123"
```

## 環境変数

- `HOST`: サーバーのホスト（デフォルト: 0.0.0.0）
- `PORT`: サーバーのポート（デフォルト: 8000）
- `API_KEY`: APIキー（デフォルト: test-key-123）

## データ形式

### 入力データ
```json
{
  "device_id": "device001",
  "breathing_rates": [12, 13, 14, 12, 15, 13, 14, 12]
}
```

### 出力データ
```json
{
  "success": true,
  "result": {
    "id": "uuid-string",
    "device_id": "device001",
    "timestamp": "2024-01-01T00:00:00",
    "breathing_rate": 13.125,
    "min_rate": 12,
    "max_rate": 15,
    "data_points": 8
  }
}
```

## 使用場面

- プロトタイプ開発
- 学習・教育目的
- 小規模な実験
- 迅速なデモンストレーション 