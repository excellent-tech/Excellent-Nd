---
name: excellent-nd
description: "Use when ChatGPT上でExcellent-Ndの導入、repository / GitHub Issue連携、既存label・Issue template・automationとの整合確認、Plan-and-Execute運用、Task Issue作成、Symphony/Codex実行、結果取り込み、人間判断ゲート、execution host bootstrapまたは引継ぎを扱う。"
---

# Excellent-Nd

Excellent-NdはオープンソースのAI駆動開発ワークフローである。ChatGPTを計画・判断の主UI、GitHub IssueをDurable Task、Symphonyを実行編成、Codexを実行workerとして扱う。

原則として日本語で応答する。ユーザーが別言語を明示した場合はその言語を優先する。

## 基本ルール

1. 通常Taskをdispatchする現在のuser messageに、case-insensitiveな `@excellent-nd` と人間による実行承認（Human GO）の両方を要求する。
2. Skillの自動選択はdispatch承認ではない。gate未成立時はPlan、調査、安全なGitHub操作までに留める。
3. ChatGPTで安全に完結するrepository調査、Issue/PR更新、小規模な設定変更、review、result ingestionをCodex dispatchより優先する。
4. 1.0.xでは原則1 Task = 1 GitHub Issue = 1 Codex threadとする。同一Taskのcontinuationは同一threadを優先する。
5. `owner` と `execution_target` を分離する。
6. 1 Issueのlifetime中は `execution_target` を固定する。host移行はcheckpoint付き後継Issueを作る。
7. target台帳は対象repositoryの `.excellent-nd/targets/*.json` を正本とし、実マシン数を固定値として扱わない。
8. credential、token、password、private key、API key等の秘密値をSkill、repository config、target台帳へ保存しない。
9. 独自Runner、DB、scheduler、notification serviceよりChatGPT / GitHub / Symphonyの既存機能を優先する。
10. 実行結果を既存Chatへ自動pushしない。ユーザーの結果取得指示時にIssue / PR / verificationを再取得する。

## 導入は3レベルで行う

### Level 1 — Skill導入

excellent-nd SkillをChatGPTへ導入し、有効であることを確認する。

Skill導入だけでは対象repositoryのIssue統合もexecution host導入も完了していない。

### Level 2 — Repository / Issue integration

execution hostを導入する前に、対象repositoryをChatGPTから監査する。詳細は `references/repository-onboarding.md` を参照する。

最低限確認する。

- 既存GitHub labelsと意味
- Issue templates / Issue forms
- GitHub Actions、bot、automationでIssue/labelを読む・更新する処理
- 既存のstatus / routing convention
- 既存 `.excellent-nd/repository.json`

各Excellent-Nd semantic roleについて、次のいずれかを決める。

- 既存labelをreuseする
- Excellent-Nd専用labelを追加する
- custom label名へmapする
- 競合が解消するまでintegrationを保留する

**名前だけで意味を推測して既存labelをreuseしない。** description、実際のIssue利用、workflow/bot設定等から意味を確認する。

承認済みmappingを対象repositoryの `.excellent-nd/repository.json` に保存する。このfileをrepository integrationのSSOTとする。

既存運用がないclean repositoryでは、ユーザーからExcellent-Nd導入指示が明示され、監査で競合が見つからなければ標準mappingを作成してよい。既存運用がある場合は、変更前にmapping proposalを提示して確認する。

Issue templateの変更は必須ではない。ChatGPT-created Excellent-Nd TaskはIssue bodyを直接作成する。既存templateやautomationと矛盾する場合、またはmanual Issue作成もExcellent-Nd形式に統一したい場合だけcustomizeする。

### Level 3 — Execution host導入

`.excellent-nd/repository.json` が存在し、labels / templates / automationのreview済み状態が確認できた場合だけexecution host setupへ進む。

setupはrepository configを読み:

- `management: existing` のlabelは存在を要求し、作成・変更しない
- `management: excellent-nd` のlabelは不足時だけ作成し、既存labelを上書きしない
- approved routing label / target prefixからWORKFLOWを生成する
- configured status labelsをobserver / resume処理でも使用する

repository integration未完了、またはexisting-managed label不足時はfail closedする。

## Plan

GO前に対象repositoryのrepository configとtarget台帳を確認し、最低限以下を提示する。

- Task分割
- 依存関係
- owner
- 概算負荷配分
- execution target案

30:70等はTask件数比ではなく概算総負荷として扱う。

## 人間による実行承認（Human GO）

現在のuser messageに `@excellent-nd` とHuman GOの両方がある場合だけ通常Taskをdispatchableにする。

Task Issueには:

- Objective
- Constraints
- Acceptance criteria
- Dependencies / owner
- relevant decisions / references
- `references/task-schema.md` のmachine-readable block

を含める。

routing/status label名は固定値を仮定せず、対象repositoryの `.excellent-nd/repository.json` を読む。

## Execute

通常Taskはrepository configで定義されたrouting labelとtarget-specific labelの両方を持つ場合だけ対象hostへdispatchする。

WORKFLOWは必ず `{{ issue.description }}` または同等手段でIssue body全体をCodex initial promptへ渡す。

Symphonyへ委ねる:

- polling
- workspace lifecycle
- transient retry
- Codex App Server起動
- thread / turn
- continuation
- concurrency

数時間・週次usage limitを短周期retryで処理しない。

## Bootstrap prerequisite

最初のhostにSymphonyがなく通常経路を利用できない場合、Human GO後にbootstrap Issueを作成し、対象host上で人間がCodex CLI等から明示的に開始する。

bootstrap前提:

1. Level 1 Skill導入済み
2. Level 2 repository integration済み
3. bootstrap Issueへtarget、verification、constraintsを保存
4. bootstrap Issue自体は通常routing対象にしない
5. setup / smoke後にtarget recordをreview・commitする
6. その後、別の通常Taskでsingle Task E2Eを行う

## 保留 / 人間判断ゲート

blocked時:

- 理由、根拠、質問をWorkpadへ保存する
- workflow statusをblockedへ更新する
- repository configで定義されたrouting labelを外す
- target identity labelはcorrelation用に維持できる
- resumeには再度 `@excellent-nd` + Human GOを要求する
- 同一Issue / thread continuationを優先する

## レビュー

review状態にはPRまたは同等のreview可能な参照とverificationを持たせる。

reviewへ遷移する同じdecision stepでrepository configのrouting labelを外す。

## 結果取り込み

ユーザーが結果取得を指示したら:

1. plan_ref / task_ref / Issue URLから関連Taskを特定する
2. Workpad、linked PR、verificationを読む
3. Task別に進捗・blocker・riskを要約する
4. 元Planへ再統合する
5. 必要がなければraw log全文を取り込まない

## Checkpoint

- branch / commit / diff: code state
- PR: review state
- Issue Workpad: decisions / verification / remaining work / blocker / handoff

## References

- repository onboarding: `references/repository-onboarding.md`
- Task schema: `references/task-schema.md`
- workflow states: `references/workflow.md`
- execution target inventory: `references/execution-targets.md`
- version policy: `references/version-policy.md`
