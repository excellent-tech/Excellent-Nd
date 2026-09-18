# Excellent-Nd

Excellent-Nd は、[OpenAI Symphony](https://github.com/openai/symphony) を基盤に、ChatGPT で考えた Plan から実行対象だけを Task として切り出し、Codex で実行する Conversation-first / ChatGPT-first の Plan-and-Execute ワークフローを目指すプロジェクトです。

> 現在は開発初期段階です。公開設計を整理し、V1 の end-to-end 実行経路を検証している段階であり、利用可能な実装はまだありません。

[简体中文](README.zh-CN.md) | [English](README.en.md)

## 解決したい問題

小人数・個人に近い開発では、要求整理、Plan、担当分割、実装、検証までを同じメンバーが横断して扱うことがあります。この場合、人間がすべての Task を手作業で Issue 化・更新すると、その管理自体が負担になります。

Excellent-Nd は ChatGPT を要求整理、Plan、担当配分、Human GO、結果確認の主 UI とし、Human GO 後の Task を GitHub Issue として Durable 化し、Symphony / Codex へ渡します。人間は Issue 管理を主 UI として意識せず、必要な結果だけを ChatGPT へ取り込みます。

会話履歴全文を Codex へ渡さず、Task ごとに目的、制約、受入条件、関連判断、参照情報を Execution Packet として渡します。結果も Codex の全文ログではなく、変更、検証、リスク、blocked、未完了事項などの構造化情報として扱います。

## 基本フロー

```text
Human + ChatGPT
  要求確認 → Plan → Task分割 / 担当配分 → Human GO
                                         ↓
GitHub Issues
  Taskごとの Execution Packet / routing
                                         ↓
Symphony
                                         ↓
Codex thread per Task
                                         ↓
Git / Test / PR / Issue Result
                                         ↓
Human: 「結果を取り込んで」
                                         ↓
ChatGPT + Human
  複数TaskのResult確認 → 元Planへ再統合 → 次の判断
```

1 つの ChatGPT Chat から 1 件以上の Task を生成できます。1 人作業では 1 Chat → 1 Task になることが多く、複数人作業では 1 Chat → 複数 Task → 複数 Codex thread に分岐できます。

V1 では、例えば「Task 1〜10 を担当Aと担当Bにおおよそ 3:7 の負荷で分ける」といった概算配分を扱います。件数比ではなく、依存関係・並列可能性・想定作業量を考慮したおおよその総負荷として解釈します。

## Symphony との関係

Symphony は Issue tracker を監視し、Issue ごとの workspace で Codex App Server を動かす orchestration の仕様と reference implementation を提供しています。

Excellent-Nd は、Symphony が提供する以下を再実装しません。

- Issue polling / dispatch
- workspace 管理
- retry / concurrency
- Codex App Server 起動
- thread / turn 管理
- continuation
- execution telemetry

V1 では、実行する Task は GitHub Issue として Durable 化し、Symphony の Issue-first execution を利用します。

つまり、人間から見た UX は Conversation-first、内部実行は Issue-first とします。

## V1 の範囲

V1 の中心は次の経路です。

> ChatGPT で Plan を作成 → 1..N Task に分割・担当配分 → Human GO → Task ごとに GitHub Issue を作成 → Symphony / Codex で実行 → GitHub に結果を保存 → 人間が「結果を取り込んで」→ ChatGPT が元 Plan に再統合する

V1 では ChatGPT への独自自動 push、独自 Codex Runner、独自 DB、独自 scheduler、独自 Kanban、大型 Web UI、multi-agent、複数 AI provider、SaaS、multi-tenant 等は実装しません。

詳細は [設計](docs/design.md)、[V1 スコープ](docs/v1-scope.md)、[未確定事項](docs/open-questions.md) を参照してください。日本語資料を設計・仕様の正本とします。


## ChatGPT Skill

Excellent-Nd の共通 ChatGPT workflow は [skills/excellent-nd](skills/excellent-nd/) で管理します。Skill は Plan 分割、Human GO、Issue 作成、machine-readable Task schema、結果取り込み、Human Gate 等の手順を再利用可能にするもので、新しい通信基盤を追加するものではありません。

Skill のインストールは **ChatGPT 側の操作規約を有効化するだけ**です。Symphony / Codex の実行環境をインストール・設定したことや、V1 の end-to-end 実装・動作確認が完了したことを意味しません。V1 の実行には、別途 execution host 上の Symphony / Codex / GitHub 連携が必要です。
