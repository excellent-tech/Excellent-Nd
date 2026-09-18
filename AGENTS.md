# AGENTS.md

## 目的

Excellent-Nd は、OpenAI Symphony を基盤に、ChatGPT 上の Plan から Human GO 後に 1 件以上の Task を GitHub Issue として実行し、結果を元の ChatGPT 会話へ取り込む Conversation-first / Plan-and-Execute ワークフローを目指す。

現段階では、公開可能な設計整理と V1 の end-to-end 検証を優先する。Symphony や Codex の実行基盤を再実装せず、未使用の将来機能を先行して増やさない。

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

- 中心フローは ChatGPT の Plan → Task分割 / 担当配分 → Human GO → GitHub Issues → Symphony / Codex → GitHub Result → 人間の明示的な取り込み → ChatGPT とする。
- 1 ChatGPT Chat から 1..N Task を生成できる。
- 原則 1 Task = 1 Codex thread とし、同じ Task の continuation は同一 thread を優先する。
- 複数 Task を複数担当へ概算負荷比率で割り当てられる。
- V1 で実行する Task は GitHub Issue として Durable 化する。
- 1 Issue の execution target は固定し、host 移行時は checkpoint を持つ後継 Issue を作る。
- active workflow state は 実行予定 / 処理中 / 保留 / レビュー とする。
- Issue は人間向け説明と Codex 向け machine-readable block を併記する。
- Symphony が提供する Issue-first orchestration は再実装しない。
- GitHub 操作は公式連携を優先し、不要なら独自 API client を作らない。
- 会話全文ではなく Execution Packet、Execution Result、Git 状態、checkpoint を受け渡す。
- ChatGPT への自動 push は V1 非対象とし、人間の「結果を取り込んで」等の明示的な pull を基本とする。
- 数時間・週次の usage limit は短周期 retry を続けず、reset 後の既存再開手段または人間の再開指示を使う。
- 共通 ChatGPT workflow は `skills/excellent-nd/` を Source of Truth とする。
- validated stable と development を分離し、stable は latest へ自動追従しない。強制更新は V1 全回帰テストを必須とする。
- 独自 Runner、独自 SQLite、独自 scheduler、独自 retry、独自 workspace manager を V1 の前提にしない。
- 独自 Kanban、大型 Web UI、中央 DB、通知基盤、multi-agent、multi-provider、SaaS、multi-tenant、汎用 workflow engine は V1 非対象とする。

## 未確定事項の扱い

未確認事項は「候補」「検証事項」と明示し、確定仕様として書かない。特に、複数 execution host の routing、Human Gate の再開、Execution Packet / Result の具体形式、usage 情報、Symphony stable release の追従方法は検証対象とする。

## 作業原則

- 確認済み事項、Excellent-Nd の設計判断、未確定事項、将来候補を区別する。
- Symphony の記述は OpenAI 公式リポジトリの現行資料を確認する。
- 実装していない機能を実装済みのように説明しない。
- 文書と実装を最小十分に保つ。
