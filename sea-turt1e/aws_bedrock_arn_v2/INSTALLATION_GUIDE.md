# Dify .env ファイルの変更手順

## 方法 1: 署名検証を無効にする（開発用）

Difyの.envファイルで以下の行を変更：

```properties
# 現在の設定
FORCE_VERIFYING_SIGNATURE=true

# 変更後
FORCE_VERIFYING_SIGNATURE=false
```

変更後、Difyを再起動：
```bash
docker-compose down
docker-compose up -d
```

## 方法 2: プラグインを適切にパッケージングする

### 2.1 プラグインパッケージの作成

```bash
# プラグインディレクトリに移動
cd /Users/yamadahikaru/project/dify-plugins/sea-turt1e/aws_bedrock_arn_v2

# パッケージファイルを作成
tar -czf aws_bedrock_arn_v2.tar.gz \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.env' \
  --exclude='test_*' \
  --exclude='validate.py' \
  --exclude='dev.sh' \
  --exclude='*.md' \
  .
```

### 2.2 ローカルファイルからのインストール

1. Dify管理画面 → **Plugins** → **Install Plugin**
2. **"Install from local file"** を選択
3. 作成した `aws_bedrock_arn_v2.tar.gz` をアップロード

## 方法 3: Development Plugin として直接実行

### 3.1 プラグインを開発モードで実行

```bash
# プラグインを実行（Difyに接続）
cd /Users/yamadahikaru/project/dify-plugins/sea-turt1e/aws_bedrock_arn_v2
python -m main
```

### 3.2 Dify管理画面での確認

1. **Settings** → **Model Providers** 
2. **Custom** セクションで **AWS Bedrock ARN** が表示されることを確認

## おすすめの手順

**開発環境では方法1（署名検証無効化）が最も簡単です：**

1. Difyの.envで `FORCE_VERIFYING_SIGNATURE=false` に設定
2. Difyを再起動
3. プラグインを直接実行: `python -m main`
4. Dify管理画面でプロバイダーが利用可能になることを確認

## トラブルシューティング

### プラグインが表示されない場合

1. プラグインのログを確認
2. Difyのplugin_daemonサービスのログを確認：
   ```bash
   docker-compose logs plugin_daemon
   ```

### 接続エラーの場合

1. ポート5003がアクセス可能か確認：
   ```bash
   netstat -an | grep 5003
   ```

2. プラグインデーモンが起動しているか確認：
   ```bash
   docker-compose ps | grep plugin_daemon
   ```
