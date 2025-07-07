#!/bin/bash

# CSI解析サーバー（Docker版）起動スクリプト

echo "=== CSI解析サーバー（Docker版）起動スクリプト ==="

# 必要なディレクトリの作成
echo "必要なディレクトリを作成しています..."
mkdir -p data/analysis data/csi data/ipfs logs

# Docker Composeの確認
if ! command -v docker-compose &> /dev/null; then
    echo "エラー: docker-composeがインストールされていません"
    echo "Docker Composeをインストールしてください: https://docs.docker.com/compose/install/"
    exit 1
fi

# Dockerの確認
if ! command -v docker &> /dev/null; then
    echo "エラー: Dockerがインストールされていません"
    echo "Dockerをインストールしてください: https://docs.docker.com/get-docker/"
    exit 1
fi

# Dockerデーモンの確認
if ! docker info &> /dev/null; then
    echo "エラー: Dockerデーモンが起動していません"
    echo "Dockerを起動してください"
    exit 1
fi

echo "Docker環境の確認が完了しました"

# 起動モードの選択
echo ""
echo "起動モードを選択してください:"
echo "1) バックグラウンド起動（推奨）"
echo "2) 開発モード（ログ表示）"
read -p "選択してください (1-2): " choice

case $choice in
    1)
        echo "バックグラウンドで起動します..."
        docker-compose up -d
        ;;
    2)
        echo "開発モードで起動します（ログ表示）..."
        docker-compose up
        ;;
    *)
        echo "無効な選択です。バックグラウンドで起動します..."
        docker-compose up -d
        ;;
esac

# 起動確認
echo ""
echo "コンテナの起動を確認しています..."
sleep 5

if docker-compose ps | grep -q "Up"; then
    echo "✅ コンテナが正常に起動しました"
    echo ""
    echo "=== アクセス情報 ==="
    echo "解析サーバーAPI: http://localhost:8000"
    echo "IPFS API: http://localhost:5001"
    echo "IPFS Gateway: http://localhost:8080"
    echo "IPFS Web UI: http://localhost:5001/webui"
    echo ""
    echo "=== 確認コマンド ==="
    echo "ヘルスチェック: curl http://localhost:8000/health"
    echo "IPFS状態: curl http://localhost:8000/ipfs/status"
    echo "ログ確認: docker-compose logs -f"
    echo "停止: docker-compose down"
else
    echo "❌ コンテナの起動に失敗しました"
    echo "ログを確認してください: docker-compose logs"
    exit 1
fi 