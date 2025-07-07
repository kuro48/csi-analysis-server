FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# システムパッケージの更新と必要なパッケージのインストール・アップグレード
RUN apt-get update && \
    apt-get install -y curl wget && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Python依存関係のコピーとインストール
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY main.py .
COPY ipfs_manager.py .
COPY docker-start.sh .
COPY analysis ./analysis
COPY api ./api

# データディレクトリの作成
RUN mkdir -p data/analysis data/csi data/ipfs logs

# ポートの公開
EXPOSE 8000

# 起動スクリプトに実行権限を付与
RUN chmod +x /app/docker-start.sh

# 起動コマンド
CMD ["/app/docker-start.sh"] 