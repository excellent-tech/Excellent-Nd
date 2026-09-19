# Excellent-Nd

Excellent-Nd は、ChatGPT を計画・判断の中心に置き、GitHub Issues、[OpenAI Symphony](https://github.com/openai/symphony)、Codex をつないで開発 Task を実行する、Conversation-first / Plan-and-Execute 型の OSS **AI-driven development workflow** です。ChatGPT 側の操作インターフェースとして excellent-nd Skill を提供します。

> 最初の通常 single Task E2E は実証済みです。現在は本番運用に向けた beta 段階で、beta candidate は `1.0.1` です。結果取り込み、continuation、複数 Task は引き続き検証します。

[简体中文](README.zh-CN.md) | [English](README.en.md)

## 解決したい問題

Excellent-Nd は、個人開発から小規模チームまでを主な利用イメージとします。この規模では、要求整理、Plan、担当分割、実装、検証までを同じ人が横断して扱うことも多く、ChatGPT と Codex の間で Task を機械的にコピー＆ペーストしたり、GitHub Issue へ転記・更新したりする作業自体が負担となり、情報や指示の漏れも生じます。同じ課題は、規模の大きな開発にも共通します。

そこで、人間と ChatGPT が要求整理、Plan、Task 分割、担当配分、Human GO を行い、Codex が Human GO 後の実作業を担います。Task は、目的、制約、受入条件、関連判断、参照情報を含む Execution Packet として GitHub Issue に Durable 化し、Symphony / Codex へ渡します。これにより機械的な転記を減らし、Issue、branch、commit、PR を通じて Task と成果を確認できるようにします。

結果は Codex の全文ログではなく、変更、検証、リスク、blocked、未完了事項などの構造化情報として扱います。人間は要求、優先順位、レビュー、最終判断など、人間が集中すべき部分に時間を使います。

[ChatGPT Plus、Pro、Business など Codex を利用できる既存プラン](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)と GitHub の既存機能を優先し、独自 Runner や独自管理基盤を増やさないことで、運用負担と追加コストを抑える考え方です。利用条件、利用上限、費用対効果はプランや開発規模によって異なります。

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

最初のexecution host、および既存経路からprovisioningできない後続hostでSymphony runtimeを導入するbootstrap Taskは限定例外です。Human GO後にGitHub Issueへ目的・受入条件・検証方法を記録し、人間が対象host上のCodex CLI等から明示的に開始します。実測version setと検証結果をIssueへ保存してruntime検証を終えた後は通常のIssue-first executionへ移行し、この例外を一般的なmanual executionへ拡大しません。

V1 では ChatGPT への独自自動 push、独自 Codex Runner、独自 DB、独自 scheduler、独自 Kanban、大型 Web UI、multi-agent、複数 AI provider、SaaS、multi-tenant 等は実装しません。

詳細は [設計](docs/design.md)、[V1 スコープ](docs/v1-scope.md)、[未確定事項](docs/open-questions.md) を参照してください。日本語資料を設計・仕様の正本とします。


## ChatGPT Skill

Excellent-Nd の共通 ChatGPT workflow は [skills/excellent-nd](skills/excellent-nd/) で管理します。Skill は Plan 分割、Human GO、Issue 作成、Task control / correlation metadata、結果取り込み、Human Gate 等の手順を再利用可能にするもので、新しい通信基盤を追加するものではありません。

Skill のインストールは **ChatGPT 側の操作規約を有効化するだけ**です。Symphony / Codex の実行環境をインストール・設定したことや、V1 の end-to-end 実装・動作確認が完了したことを意味しません。V1 の実行には、別途 execution host 上の Symphony / Codex / GitHub 連携が必要です。

## 責務と利用ガイド

| Component | 責務 |
| --- | --- |
| Excellent-Nd | OSS project / AI-driven development workflow |
| excellent-nd Skill | ChatGPT 側の計画・Human GO・操作インターフェース |
| GitHub | Durable Task、Execution Packet、checkpoint、PR / Result |
| Symphony | Issue-first execution orchestration |
| Codex | Task execution worker |

導入、運用、FAQ、uninstall、version、label、`execution_target` は [利用ガイド](docs/operations.md) を参照してください。
