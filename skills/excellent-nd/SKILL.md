---
name: excellent-nd
description: "ChatGPTでExcellent-NdのConversation-first / Plan-and-Execute運用を行うときに使用する。Human GO後にPlanを1件以上のGitHub実行Taskへ分割し、担当・概算負荷を割り当て、人間向け説明と機械可読情報を併記したIssueを作成・更新する。Issue/PR/test結果を元のPlanへ取り込み、保留、レビュー、継続、host routing、引継ぎを一貫したルールで扱う。共通・公開可能な運用規約だけを扱い、組織固有のプロジェクト名、host名、credential、内部運用情報は含めない。"
---

# Excellent-Nd

ChatGPTを計画・判断の主UIとして使い、GitHub IssueをDurable Taskの封筒、Symphony / Codexを実行経路として扱う。

原則として日本語で応答する。ユーザーが別言語を明示した場合は、その言語を優先する。

このSkillのインストールはChatGPT側のworkflowを有効化するだけであり、Symphony / Codex runtimeの導入完了やV1 end-to-end動作確認完了を意味しない。実行環境が未検証の場合は、実装済み・稼働済みのように説明しない。

## 基本ルール

1. 明示的なHuman GO前に実行Taskを開始しない。
2. 1つのChatGPTチャットを計画・判断コンテキストとして扱い、そこから1..N Taskへ分岐できる。
3. V1では実行Taskごとに1つのGitHub Issueを作る。
4. 原則として1 Task = 1 Codex threadとする。同一Taskの継続では、利用可能なら同じthreadを再利用する。
5. ユーザーが明示的にthread分割を指示した場合、contextが信頼できなくなった場合、resumeできない場合は新threadへ引き継ぐ。全文履歴ではなくGit状態とcheckpointを引き継ぐ。
6. `owner` と `execution_target` を分離して扱う。
7. 1 Issueのlifetime中は `execution_target` を固定する。別hostへ移す場合は後継Issueを作り、旧Issueと新Issueを相互参照する。
8. 実行結果を既存Chatへ自動pushしない。ユーザーが結果取得・状況確認を指示したときにGitHubのIssue / PR / verificationを取得し、Planへ再統合する。
9. 独自Runner、DB、scheduler、notification service、Codex App Server clientより、既存のChatGPT / GitHub / Symphony機能を優先する。
10. private project名、内部host名、credential、token、組織固有の運用情報を共通Skillへ入れない。

## ワークフロー

### 1. Plan

ユーザーとPlanを作り、実行Taskを識別する。

GO前に、最低限以下を提示する。

- Task分割
- 依存関係
- owner割当
- 概算負荷配分
- execution target案

30:70等の比率はTask件数比ではなく、おおよその総作業負荷として解釈する。依存関係、並列実行可否、想定工数を考慮する。

### 2. Human GO

明示的なGO後にのみ、実行対象のGitHub Issueを作成または更新する。

各Issueには以下を含める。

- 人間が読めるTask説明
- acceptance criteria
- constraints
- dependencies
- owner
- `references/task-schema.md` に従うmachine-readable block
- 利用中のSymphony profileが必要とするrouting label / field

workflow stateは `references/workflow.md` に従う。

### 3. Execute

Issueを固定された `execution_target` へroutingする。

以下はSymphonyへ委ねる。

- polling
- workspace lifecycle
- 一時エラーのretry
- Codex App Server起動
- thread / turn管理
- continuation
- concurrency

数時間・週次のusage limitを通常の短周期retryで処理しない。account usage枯渇時は `references/workflow.md` のrate-limit方針に従う。

### 4. 保留 / Human Gate

人間判断が必要な場合:

- Taskを `blocked` / 保留へ変更する
- Issue Workpadへ理由、根拠、具体的な質問を保存する
- そのIssueの実行routingを停止する
- ユーザーが状況・結果を取得したときに判断事項を提示する
- ユーザー回答後、決定内容をIssueへ保存し、同じIssueを再度実行可能にする
- 同一Codex threadのcontinuationを優先する

### 5. レビュー

IssueをTaskのWorkpad / 状態記録として使う。

PRをコード変更・レビュー成果物として使う。

`review` / レビュー状態のTaskには、原則としてPRまたは同等のreview可能な変更参照とverification結果を持たせる。

### 6. 結果取り込み

ユーザーが「結果を取り込んで」「状況確認して」「担当A/Bの進捗をまとめて」等と指示した場合:

1. 元Planと関連Task Issueを特定する。
2. 各Issue Workpadとlinked PRを読む。
3. test / verification statusと必要なGit事実を取得する。
4. Task別・owner別に要約する。
5. Plan全体の進捗、blocker、risk、次の判断を再構成する。
6. ユーザーが必要としない限りraw log全文を取り込まない。

## Checkpoint

V1のcheckpointは以下とする。

- Git branch / commit / diff: コード状態
- PR: review可能な変更状態
- Issue Workpad: 判断、完了作業、verification、残作業、blocker、handoff情報

V1では別repository artifactや独自DBを必須にしない。

## Version管理

常にlatestへ追従せず、検証済みversion setとして実行stackを扱う。詳細は `references/version-policy.md` を参照する。
