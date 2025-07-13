# ai-infra setup guide

LiteLLM + Langfuse v3

## 前提条件

- Docker & Docker Compose
- dotenvx (環境変数暗号化ツール)
- 各種API Key (OpenAI, Anthropic, Gemini等)

## 1. 初期セットアップ

### 1.1 認証キーの生成

```bash
./setup.sh
```

### 1.2 環境変数の設定

必要なAPIキーを設定します：

```bash
dotenvx set OPENAI_API_KEY your_openai_key
dotenvx set ANTHROPIC_API_KEY your_anthropic_key  
dotenvx set GEMINI_API_KEY your_gemini_key
dotenvx set LITELLM_MASTER_KEY your_generated_master_key
```

### 1.3 初回起動

```bash
dotenvx run -- docker compose up -d
```

## 2. Langfuse 初期設定

### 2.1 サービス起動確認

全コンテナが正常に起動するまで待機します：

```bash
docker compose ps
```

### 2.2 Langfuse WebUI アクセス

ブラウザで `http://localhost:3000` にアクセスします。

### 2.3 アカウント作成

初回アクセス時はサインアップが必要です：

1. Sign up ページにアクセス
2. 以下の情報を入力：
   - Name: `Admin User`
   - Email: `admin@example.com`
   - Password: `Admin123!@#` (文字、数字、特殊文字を含む安全なパスワード)
3. Sign up ボタンをクリック

### 2.4 組織作成

サインアップ後、組織設定ページにリダイレクトされます：

1. New Organization をクリック
2. Organization name に `AI Infrastructure` を入力
3. Create ボタンをクリック

### 2.5 プロジェクト作成

組織作成後、プロジェクト作成に進みます：

1. Next ボタンをクリック（メンバー招待をスキップ）
2. Project name に `Default Project` を入力
3. Create ボタンをクリック

### 2.6 APIキー生成

プロジェクト作成後、APIキー生成ページが表示されます：

1. Create API Key ボタンをクリック
2. 生成されたキーをメモ：
   - Public Key: `pk-lf-xxxxxxxxxx`
   - Secret Key: `sk-lf-xxxxxxxxxx`
   - Host: `http://localhost:3000`

## 3. LiteLLM設定更新

### 3.1 環境変数更新

生成されたAPIキーで環境変数を更新します：

```bash
dotenvx set LANGFUSE_HOST http://langfuse-web:3000
dotenvx set LANGFUSE_PUBLIC_KEY pk-lf-xxxxxxxxxx
dotenvx set LANGFUSE_SECRET_KEY sk-lf-xxxxxxxxxx
```

### 3.2 コンテナ再起動

新しい設定を適用するため、全コンテナを再起動します：

```bash
dotenvx run -- docker compose down
dotenvx run -- docker compose up -d
```

### 3.3 起動確認

全サービスが起動するまで待機（約30秒）：

```bash
sleep 30
docker compose ps
```

## 4. 動作確認

### 4.1 LiteLLM健康状態チェック

```bash
dotenvx run -- sh -c 'curl -H "Authorization: Bearer $LITELLM_MASTER_KEY" http://localhost:4000/health'
```

### 4.2 トレーシング機能テスト

```bash
dotenvx run -- sh -c 'curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -d '"'"'{
    "model": "gpt-4.1-nano",
    "messages": [
      {"role": "user", "content": "Test message for tracing"}
    ],
    "max_tokens": 30
  }'"'"
```

### 4.3 Langfuse WebUIでトレース確認

1. ブラウザで `http://localhost:3000` にアクセス
2. 作成したアカウントでログイン
3. プロジェクトページ → Traces セクションに移動
4. APIリクエストのトレースが表示されることを確認

## 5. サービス一覧

セットアップ完了後、以下のサービスが利用可能になります：

| サービス | ポート | URL | 説明 |
|---------|--------|-----|------|
| LiteLLM Proxy | 4000 | http://localhost:4000 | LLMプロキシサーバー |
| Langfuse Web | 3000 | http://localhost:3000 | LLM観測プラットフォーム |
| PostgreSQL | 5432 | - | メタデータストレージ |
| Redis | 6379 | - | キャッシュストレージ |
| ClickHouse | 8123 | - | 分析データベース |
| MinIO | 9190 | - | オブジェクトストレージ |

## 6. トラブルシューティング

### 6.1 Langfuse 401 Unauthorized エラー

APIキーが正しく設定されていない場合に発生します：

```bash
# コンテナ内の環境変数を確認
docker exec ai-infra-litellm-1 env | grep LANGFUSE

# 正しいキーが設定されていない場合は再設定
dotenvx set LANGFUSE_PUBLIC_KEY correct_public_key
dotenvx set LANGFUSE_SECRET_KEY correct_secret_key
```

### 6.2 トレースが表示されない

1. LiteLLMログでエラーがないか確認：
```bash
docker logs ai-infra-litellm-1 --tail 20
```

2. Langfuse WebUIをリフレッシュ（F5キー）
3. 時間フィルターを確認（過去24時間に設定）

### 6.3 コンテナ起動失敗

依存関係の順序で起動に失敗する場合：

```bash
# 個別に起動
docker compose up -d postgres redis clickhouse minio
sleep 10
docker compose up -d langfuse-web langfuse-worker
sleep 10
docker compose up -d litellm
```
