"""
メッセージ分類カスタムコールバック

GPT-5 Nanoを使用して各リクエストのメッセージを開発フェーズごとに分類します:
- レビュー
- 設計
- 実装
- テスト
- その他
"""
from litellm.integrations.custom_logger import CustomLogger
import litellm
import os
import json


class MessageClassifier(CustomLogger):
    """
    メッセージを開発フェーズごとに分類するコールバック
    """

    def __init__(self):
        super().__init__()
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        print("[MessageClassifier] Initialized")

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        """
        成功したリクエストの後に分類を実行
        """
        print("[MessageClassifier] async_log_success_event called")
        await self._classify_message(kwargs)

    async def _classify_message(self, kwargs):
        """メッセージ分類の共通ロジック"""
        try:
            # メッセージ抽出
            messages = kwargs.get("messages", [])
            print(f"[MessageClassifier] Messages found: {len(messages) if messages else 0}")
            if not messages:
                print("[MessageClassifier] No messages to classify")
                return

            # 最後のユーザーメッセージを取得
            user_message = None
            for msg in reversed(messages):
                if isinstance(msg, dict) and msg.get("role") == "user":
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        user_message = content
                    elif isinstance(content, list):
                        # content が配列の場合、text部分を抽出
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "text":
                                user_message = item.get("text", "")
                                break
                    break

            if not user_message:
                print("[MessageClassifier] No user message found")
                return

            # GPT-5 Nanoで分類 - Responses APIとminimal reasoning effortを使用
            # プロンプトキャッシング最適化: 静的コンテンツを前に配置
            import litellm
            from litellm import aresponses

            # システムプロンプト
            # 1024トークンにしてプロンプトキャッシングを有効化
            system_prompt = """あなたは開発プロジェクトのメッセージを分類する専門的なAIアシスタントです。
ソフトウェア開発のライフサイクルにおける様々な活動を正確に分類することがあなたの役割です。

# 分類カテゴリの詳細定義

## 1. レビュー（Review）
コードレビューや品質チェックに関連する活動を指します。

### 含まれる活動:
- コードレビュー依頼と実施
- プルリクエストのレビュー
- コード品質の評価とフィードバック
- 静的解析結果の確認
- セキュリティレビュー
- パフォーマンスレビュー
- アーキテクチャレビュー
- 改善提案の検討と評価
- ベストプラクティスへの適合性チェック
- 技術的負債の特定と評価

### 典型的なキーワード:
レビュー、review、PR、pull request、チェック、確認、評価、フィードバック、改善、品質

## 2. 設計（Design）
システムやコンポーネントの設計に関する活動を指します。

### 含まれる活動:
- システムアーキテクチャの設計
- マイクロサービス設計
- API設計とインターフェース定義
- データベース設計（スキーマ、正規化、インデックス）
- データモデリング
- クラス設計とオブジェクト指向設計
- デザインパターンの適用
- 技術スタックの選定
- フレームワークやライブラリの選択
- セキュリティアーキテクチャ設計
- スケーラビリティ設計
- 可用性と冗長性の設計
- インフラストラクチャ設計
- 技術仕様書の作成
- 要件定義と技術的実現方法の検討

### 典型的なキーワード:
設計、design、アーキテクチャ、architecture、API、データベース、DB、スキーマ、モデル、仕様、spec、技術選定

## 3. 実装（Implementation）
実際のコーディングや開発作業を指します。

### 含まれる活動:
- 新機能の実装とコーディング
- バグ修正とデバッグ
- リファクタリングとコード改善
- パフォーマンス最適化
- セキュリティ脆弱性の修正
- 技術的負債の解消
- 依存関係の更新
- コードのクリーンアップ
- ドキュメント化（コメント、README等）
- CI/CDパイプラインの構築
- 環境構築とセットアップ
- データマイグレーション
- 統合作業

### 典型的なキーワード:
実装、implement、開発、develop、コーディング、coding、修正、fix、バグ、bug、リファクタ、refactor、機能追加

## 4. テスト（Testing）
テストの作成、実行、品質保証活動を指します。

### 含まれる活動:
- ユニットテストの作成と実行
- 統合テストの作成と実行
- E2Eテスト（End-to-End）の作成と実行
- パフォーマンステスト
- 負荷テスト、ストレステスト
- セキュリティテスト
- UI/UXテスト
- 回帰テスト
- テストカバレッジの向上
- テストケースの設計と作成
- テストデータの準備
- テスト自動化
- QA活動全般
- テスト結果の分析と報告

### 典型的なキーワード:
テスト、test、testing、ユニットテスト、unit test、E2E、統合テスト、QA、カバレッジ、coverage

## 5. その他（Other）
上記4つのカテゴリに明確に該当しない活動を指します。

### 含まれる活動:
- 一般的な会話や挨拶
- プロジェクト管理や進捗確認
- ドキュメント作成（技術文書以外）
- ミーティングや相談
- 学習や調査
- 環境に関する質問
- ツールの使い方に関する質問
- その他の雑多な活動

# 出力形式の厳密な定義

必ず以下のJSON形式で出力してください。マークダウンのコードブロックは使用しないでください：

{"category": "カテゴリ名", "confidence": 信頼度}

## パラメータ仕様:
- **category**: 必ず以下のいずれか1つ: "レビュー", "設計", "実装", "テスト", "その他"
- **confidence**: 0.0から1.0の範囲の浮動小数点数

## 信頼度の目安:
- 0.9以上: カテゴリが明確で疑いの余地がない
- 0.7-0.9: カテゴリがかなり明確だが、わずかに他の解釈も可能
- 0.5-0.7: カテゴリの判断が難しいが、最も可能性が高い選択
- 0.5未満: 非常に曖昧で、複数のカテゴリの可能性がある

# 分類の詳細ルール

## 優先順位:
1. メッセージの主要な目的や意図を最優先で考慮する
2. 明示的なアクション要求がある場合は、そのアクションに基づいて分類
3. 複数の要素が含まれる場合は、最も支配的（文脈上重要）な要素で判断

## 境界ケースの処理:
- 「設計レビュー」→ 主目的がレビューなら「レビュー」
- 「実装とテスト」→ 最も強調されている方を選択、同等なら実装を優先
- 「〜について相談したい」→ 相談内容の主題で分類（設計相談なら「設計」）

## 不明確な場合:
- 情報が不足している場合は「その他」を選択
- confidenceを0.5以下に設定
- コンテキストから推測可能な場合は、合理的な推測を行う

# 分類例（参考）

## レビューカテゴリの例:
- "このPRをレビューしてください" → {"category": "レビュー", "confidence": 0.95}
- "コード品質をチェックお願いします" → {"category": "レビュー", "confidence": 0.92}
- "セキュリティ観点でレビュー" → {"category": "レビュー", "confidence": 0.93}
- "パフォーマンス改善の提案を確認" → {"category": "レビュー", "confidence": 0.88}
- "設計のレビューをお願い" → {"category": "レビュー", "confidence": 0.80}
- "コードの改善点を指摘してください" → {"category": "レビュー", "confidence": 0.91}

## 設計カテゴリの例:
- "API仕様について相談したい" → {"category": "設計", "confidence": 0.92}
- "データベーススキーマを設計" → {"category": "設計", "confidence": 0.94}
- "マイクロサービスのアーキテクチャ検討" → {"category": "設計", "confidence": 0.91}
- "技術スタックの選定について" → {"category": "設計", "confidence": 0.89}
- "システム全体の設計図を作成" → {"category": "設計", "confidence": 0.93}
- "REST APIのエンドポイント設計" → {"category": "設計", "confidence": 0.92}

## 実装カテゴリの例:
- "新機能を実装しました" → {"category": "実装", "confidence": 0.94}
- "バグを修正" → {"category": "実装", "confidence": 0.93}
- "リファクタリングを実施" → {"category": "実装", "confidence": 0.91}
- "認証機能を追加" → {"category": "実装", "confidence": 0.92}
- "テストコードを実装" → {"category": "実装", "confidence": 0.75}
- "依存関係を更新しました" → {"category": "実装", "confidence": 0.87}

## テストカテゴリの例:
- "ユニットテストを追加" → {"category": "テスト", "confidence": 0.94}
- "E2Eテストの実行結果を確認" → {"category": "テスト", "confidence": 0.92}
- "カバレッジを向上させる" → {"category": "テスト", "confidence": 0.90}
- "統合テストを作成" → {"category": "テスト", "confidence": 0.93}
- "負荷テストを実施" → {"category": "テスト", "confidence": 0.91}

## その他カテゴリの例:
- "おはようございます" → {"category": "その他", "confidence": 0.98}
- "進捗はどうですか？" → {"category": "その他", "confidence": 0.85}
- "ミーティングの日程調整" → {"category": "その他", "confidence": 0.87}
- "この技術について教えてください" → {"category": "その他", "confidence": 0.82}

これらのfew-shot例に従って、提示されたメッセージを正確に分類してください。"""

            classification_response = await aresponses(
                model="gpt-5-nano",
                input=[
                    {"role": "developer", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                api_key=self.openai_api_key,
                reasoning={"effort": "minimal"},  # 推論トークンを最小化
                prompt_cache_key="message_classifier_v1",  # 明示的なキャッシュキー
            )

            # Responses APIのレスポンスから出力テキストを取得
            print(f"[MessageClassifier] Response status: {classification_response.status}")

            # キャッシュヒット状況を確認
            if hasattr(classification_response, 'usage'):
                usage = classification_response.usage
                print(f"[MessageClassifier] Usage: input={usage.input_tokens}, output={usage.output_tokens}, cached={usage.input_tokens_details.cached_tokens if hasattr(usage, 'input_tokens_details') else 0}")

            # outputから ResponseOutputMessage を探してtextを取得
            classification_text = None
            if hasattr(classification_response, 'output') and classification_response.output:
                for item in classification_response.output:
                    if item.type == 'message' and hasattr(item, 'content'):
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                classification_text = content_item.text
                                break
                        if classification_text:
                            break

            print(f"[MessageClassifier] Extracted text: {classification_text}")

            if not classification_text or classification_text.strip() == "":
                print("[MessageClassifier] Empty response from GPT-5 Nano")
                category = "その他"
                confidence = 0.5
            else:
                # JSONを抽出（マークダウンコードブロックの可能性も考慮）
                text = classification_text.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()

                classification_data = json.loads(text)
                category = classification_data.get("category", "その他")
                confidence = classification_data.get("confidence", 0.0)

            # メタデータに分類結果を追加
            print(f"[MessageClassifier] Category: {category} (confidence: {confidence:.2f})")
            print(f"[MessageClassifier] Original model: {kwargs.get('model')}")
            print(f"[MessageClassifier] Message preview: {user_message[:100]}...")

            # Langfuseなどの他のコールバックで利用できるようにkwargsに追加
            if "metadata" not in kwargs:
                kwargs["metadata"] = {}
            kwargs["metadata"]["message_category"] = category
            kwargs["metadata"]["category_confidence"] = confidence

        except Exception as e:
            print(f"[MessageClassifier] Error during classification: {e}")
            # 分類失敗してもメインのリクエストには影響させない
            pass

    def log_success_event(self, kwargs, response_obj, start_time, end_time):
        """
        同期版の成功イベント処理
        """
        print("[MessageClassifier] log_success_event called (sync)")
        print(f"[MessageClassifier] kwargs keys: {list(kwargs.keys()) if kwargs else 'None'}")
        print(f"[MessageClassifier] response type: {type(response_obj)}")
        # 同期版では分類を実行しない（非同期版のみで実行）
        pass


message_classifier = MessageClassifier()
