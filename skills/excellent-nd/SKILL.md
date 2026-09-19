---
name: excellent-nd
description: "Use when ChatGPT上でExcellent-NdのPlan-and-Execute運用、Task Issue作成、Symphony実行、結果取り込み、Human Gate、host bootstrapまたは引継ぎを扱う。"
---

# Excellent-Nd

Excellent-NdはOSSのAI-driven development workflowである。ChatGPTを計画・判断の主UI、excellent-nd Skillを操作interface、GitHubをDurable Task / checkpoint、Symphonyをexecution orchestration、Codexをexecution workerとして扱う。

原則として日本語で応答する。ユーザーが別言語を明示した場合は、その言語を優先する。

このSkillのインストールはChatGPT側のworkflowを有効化するだけであり、Symphony / Codex runtimeの導入完了やV1 end-to-end動作確認完了を意味しない。実行環境が未検証の場合は、実装済み・稼働済みのように説明しない。

## 基本ルール

1. 明示的なHuman GO前に実行Taskを開始しない。
2. 1つのChatGPTチャットを計画・判断コンテキストとして扱い、そこから1..N Taskへ分岐できる。
3. V1では実行Taskごとに1つのGitHub Issueを作る。通常TaskはIssue → Symphony → Codexで実行する。
4. 原則として1 Task = 1 Codex threadとする。同一Taskの継続では、利用可能なら同じthreadを再利用する。
5. ユーザーが明示的にthread分割を指示した場合、contextが信頼できなくなった場合、resumeできない場合は新threadへ引き継ぐ。全文履歴ではなくGit状態とcheckpointを引き継ぐ。
6. `owner` と `execution_target` を分離して扱う。
7. `execution_target` は同一LAN / 組織管理範囲で一意なhost hostnameを基本identityとし、Issue lifetime中は固定する。移行は後継Issueを作る。public repositoryでは必要に応じnon-sensitive hostname / public aliasを使い、mappingは公開artifact外に保持する。
8. 実行結果を既存Chatへ自動pushしない。ユーザーが結果取得・状況確認を指示したときにGitHubのIssue / PR / verificationを取得し、Planへ再統合する。
9. 独自Runner、DB、scheduler、notification service、Codex App Server clientより、既存のChatGPT / GitHub / Symphony機能を優先する。
10. private project名、内部host名、credential、token、組織固有の運用情報を共通Skillへ入れない。
11. Symphony未導入hostのruntime bootstrapは通常Taskと区別し、Human GOとIssue記録を維持した限定例外として扱う。

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
- objective、constraints、acceptance criteria
- relevant decisions / references
- dependencies、owner
- `references/task-schema.md` に従うTask control / correlation metadata block
- 通常Taskでは、利用中のSymphony profileが必要とするrouting label / field
- routing用 `symphony-ready` と可視化用 `nd-status:scheduled|running|blocked|review|failed`（原則1つ）

workflow stateは `references/workflow.md` に従う。

### 2a. Bootstrap prerequisite

最初のexecution hostにSymphony runtimeがなく、通常経路をまだ利用できない場合だけ、次のbootstrap規約を使う。

1. Human GO後にGitHub Issueを作り、objective、constraints、acceptance criteria、execution target、verification方法を記録する。
2. 利用可能なSymphony profileはまだ存在しないため、通常Task用routing label / fieldは要求せず、execution-control条件を付けない。既存profileがある場合もbootstrap Issueを選択できない状態にする。
3. Issueを監査可能な作業記録として、対象host上のCodex CLI等から人間が明示的にbootstrapを開始する。
4. Symphonyの導入とversion、Codex App Server利用可能性、Git / GitHub接続、WORKFLOW / profile読込、routing条件が既存Issueを意図せずdispatchしないことまでをsmoke verificationする。
5. 実測version setとverification結果をIssueへ保存し、bootstrapを完了する。
6. bootstrap完了後、別の通常Task Issueへrouting条件を適用し、single Task E2Eを実施する。このE2Eはbootstrapのacceptance criteriaに含めない。

この例外を一般的なmanual executionへ拡大しない。2台目以降も、既存のExcellent-Nd / Symphony経路からprovisioningできないhostに限り同じ規約を使い、V1では自動provisioning機構を作らない。

### 3. Execute

通常の実行Taskは、Issueを固定された `execution_target` へroutingし、SymphonyからCodexへ渡す。target未確定の通常Taskをdispatchableにしない。

runtime / profileは、initial Codex turnのrendered promptへIssue body由来の `issue.description` を必ず含める。custom `WORKFLOW.md` promptを使う場合も `{{ issue.description }}` または同等の方法でExecution Packet全体をrenderし、titleだけを渡す構成にしない。

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
- そのIssueのexecution-control条件を外し、実行routingを停止する。`execution_target` のidentityは維持する
- ユーザーが状況・結果を取得したときに判断事項を提示する
- ユーザー回答後、決定内容をIssueへ保存し、同じIssueを再度実行可能にする
- 同一Codex threadのcontinuationを優先する

### 5. レビュー

IssueをTaskのWorkpad / 状態記録として使う。

PRをコード変更・レビュー成果物として使う。

`review` / レビュー状態のTaskには、原則としてPRまたは同等のreview可能な変更参照とverification結果を持たせる。

### 6. 結果取り込み

ユーザーが「結果を取り込んで」「状況確認して」「担当A/Bの進捗をまとめて」等と指示した場合:

1. `plan_ref` と `task_ref` の組、元Planに保存したGitHub Issue URL / numberから関連Task Issueを特定する。
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
