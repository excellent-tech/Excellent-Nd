# AGENTS.md

## 目的

Excellent-Nd は、OpenAI Symphony を基盤に、ChatGPT で計画し、人間の GO 後に必要な 1 Task を Codex で実行する Conversation-first / Plan-and-Execute ワークフローを目指す。

現段階では、公開可能な設計整理と V1 の検証を優先する。Symphony や Codex の実行基盤を再実装せず、未使用の将来機能を先行して増やさない。

## 公開情報の制約

このリポジトリは公開 OSS である。以下を文書、Issue、PR、コメント、サンプル、テストデータへ含めないこと。

- 社内事情、組織固有の運用事情、顧客情報、非公開インフラ情報
- 別プロジェクト固有の名称、構成、コード、パス、Issue、業務情報
- 個人情報、認証情報、トークン、秘密鍵、内部 URL

背景から得た要件は、Excellent-Nd に必要な一般化された技術要件としてのみ記述する。

## 言語

- 設計書・仕様書は日本語を正本とする。
- `README.md` は日本語、`README.zh-CN.md` は簡体字中国語、`README.en.md` は英語とする。
- 設計判断や仕様変更は、まず日本語資料へ反映する。

## V1 の方針

- 中心フローは ChatGPT の Plan → Human GO → 1 Task → Codex 実行 → 構造化 Result → ChatGPT とする。
- Issue 化しない lightweight Task と、GitHub Issue を使う Durable Task を区別する。
- Symphony が提供する Issue-first orchestration は再実装しない。
- GitHub 操作は公式連携を優先し、不要なら独自 API client を作らない。
- 会話全文ではなく Execution Packet、Execution Result、Git 状態、checkpoint を受け渡す。
- 同じ Task の継続は同一 Codex thread、別 Task は新規 thread を基本とする。
- 独自 Runner、独自 SQLite、独自 scheduler、独自 retry、独自 workspace manager を V1 の前提にしない。
- 独自 Kanban、大型 Web UI、中央 DB、通知基盤、multi-agent、multi-provider、SaaS、multi-tenant、汎用 workflow engine は V1 非対象とする。

## 未確定事項の扱い

未確認事項は「候補」「検証事項」と明示し、確定仕様として書かない。特に、ChatGPT から実行開始までの経路、lightweight Task の実行方法、結果返却、Human Gate の再開、usage 情報、Symphony reference implementation の利用形態は検証対象とする。

## 作業原則

- 確認済み事項、Excellent-Nd の設計判断、未確定事項、将来候補を区別する。
- Symphony の記述は OpenAI 公式リポジトリの現行資料を確認する。
- 実装していない機能を実装済みのように説明しない。
- 文書と実装を最小十分に保つ。
