# Excellent-Nd

Excellent-Nd は、[OpenAI Symphony](https://github.com/openai/symphony) を基盤に、ChatGPT で考えた計画から必要な作業だけを Codex へ渡す、Conversation-first / ChatGPT-first の Plan-and-Execute ワークフローを目指すプロジェクトです。

> 現在は開発初期段階です。公開設計を整理し、V1 の実行経路を検証している段階であり、利用可能な実装はまだありません。

[简体中文](README.zh-CN.md) | [English](README.en.md)

## 解決したい問題

小人数・個人に近い開発では、相談、調査、細かな作業をすべて Issue 化すると、その管理自体が負担になります。一方、会話履歴の全文を実行エージェントへ渡す方法は、不要な文脈とトークン消費を増やします。

Excellent-Nd は ChatGPT を要求整理、計画、判断の主 UI とし、人間が承認した実行対象だけを小さな Task にまとめます。Codex へは目的、制約、受入条件、関連判断、参照情報を渡し、結果は変更、検証、リスク、未完了事項などの構造化情報として ChatGPT に戻します。

## 基本フロー

```text
Human + ChatGPT: 要求確認 → Plan → Human GO
                                  ↓
Excellent-Nd workflow:       1 Task を準備
                                  ↓
Symphony / Codex:       実装・調査・検証
                                  ↓
ChatGPT + Human:       Result 確認 → 次の判断
```

これを Conversation-first / Plan-and-Execute と呼びます。すべての思考を Issue にせず、短時間・単独の作業は lightweight Task、共有・引継ぎ・長期履歴・Human Gate が必要な作業は GitHub Issue を使う Durable Task として扱います。V1 ではこの分類の自動化は行いません。

## Symphony との関係

Symphony は Issue tracker を監視し、Issue ごとの workspace で Codex App Server を動かす orchestration の仕様と reference implementation を提供しています。Excellent-Nd は、その実行管理、workspace、retry、concurrency、thread / turn 管理、実行テレメトリを再実装しません。

Symphony が得意とする Issue-first execution を Durable Task に利用しつつ、Excellent-Nd は ChatGPT 上の Plan から実行に必要な情報だけを切り出し、結果を会話へ戻す境界に集中します。Issue 化しない lightweight Task の最小実行経路は未確定で、V1 の事前検証事項です。

## V1 の範囲

V1 の中心は次の 1 本の経路です。

> ChatGPT で Plan を作成 → Human GO → 1 Task を Codex へ渡す → 実行 → 構造化 Result を ChatGPT から確認する

ChatGPT を主 UI、Codex が動作する Git 管理下の開発環境を実行先、Symphony を Issue-first orchestration の基盤、GitHub を必要な場合の Issue・PR・共有履歴として利用します。

独自 Codex Runner、独自 agent harness、独自 Kanban、大型 Web UI、中央 DB、通知基盤、multi-agent、複数 AI provider、SaaS、multi-tenant、汎用 workflow engine は V1 の対象外です。

詳細は [設計](docs/design.md)、[V1 スコープ](docs/v1-scope.md)、[未確定事項](docs/open-questions.md) を参照してください。日本語資料を設計・仕様の正本とします。
