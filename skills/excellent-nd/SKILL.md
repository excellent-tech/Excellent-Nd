---
name: excellent-nd
description: "Use when ChatGPT上でExcellent-Ndの導入、repository / GitHub Issue連携、既存label・GitHub Project Field・Issue template・automationとの汎用mapping、dispatch gate、Plan-and-Execute運用、Task Issue作成、Symphony/Codex実行、結果取り込み、人間判断ゲート、execution host bootstrapまたは引継ぎを扱う。"
---

# Excellent-Nd

Excellent-NdはオープンソースのAI駆動開発ワークフローである。ChatGPTを計画・判断の主UI、GitHub IssueをDurable Task、Symphonyを実行編成、Codexを実行workerとして扱う。

原則として日本語で応答する。ユーザーが別言語を明示した場合はその言語を優先する。

## 基本ルール

1. 新しいTaskまたはPlanを初回dispatchする前に、現在のuser messageで実行意図が明示されていることを要求する。`@excellent-nd` は明示方法の1つだが必須構文ではない。「この計画で進めて」「実行して」等の明確な実行指示も有効とする。Skillの自動選択や単なる相談・計画依頼は実行指示とみなさない。
2. 複数Taskを含むPlan全体が人間により実行指示された場合、既定ではそのPlan配下の事前定義Taskへ実行権限を継承する。TaskごとのIssue番号やExcellent-Nd内部操作を人間へ要求しない。
3. ChatGPTで安全に完結するrepository調査、Issue/PR更新、小規模な設定変更、review、result ingestionをCodex dispatchより優先する。
4. 1.0.xでは原則1 Task = 1 GitHub Issue = 1 Codex threadとする。同一Taskのcontinuationは同一threadを優先する。
5. `owner` と `execution_target` を分離する。
6. 1 Issueのlifetime中は `execution_target` を固定する。host移行はcheckpoint付き後継Issueを作る。
7. target台帳は対象repositoryの `.excellent-nd/targets/*.json` を正本とし、実マシン数を固定値として扱わない。
8. credential、token、password、private key、API key等の秘密値をSkill、repository config、target台帳へ保存しない。
9. 独自Runner、DB、scheduler、notification serviceよりChatGPT / GitHub / Symphonyの既存機能を優先する。
10. 実行結果を既存Chatへ自動pushしない。ユーザーの結果取得指示時にIssue / PR / verificationを再取得する。
11. public Excellent-Nd repository、Issue、PR、example、artifactへprivate repository名、内部Project title、識別可能な内部workflow値を転記しない。public exampleは匿名・汎用値だけを使う。

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

各Excellent-Nd semantic roleについて、既存repositoryの正本を優先してmappingする。

- status authorityが既存Labelなら `authority: labels` を使う
- status authorityがGitHub Project Fieldなら `authority: github-project` を使い、status labelを作らない
- repository固有のField名や値をExcellent-Nd Coreへhard-codeせず、`status_integration.event_mapping` と `dispatch_gates[]` へ設定する
- dispatch gateは `github-project-field` / `label` / `issue-state` を組み合わせる
- routing / execution targetはExcellent-Nd固有metadataとして分離できる
- 個別repository固有の名前・Field値はCoreへ持ち込まず、repository-local configだけで扱う

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
- `authority: labels` ではconfigured status labelsをobserver / resume処理で使用する
- `authority: github-project` ではstatus labelsを生成せず、Project Fieldを状態正本として扱う

repository integration未完了、またはexisting-managed label不足時はfail closedする。

## Plan

dispatch前に対象repositoryのrepository configとtarget台帳を確認し、最低限以下を提示する。

- Task分割
- 依存関係
- owner
- 概算負荷配分
- execution target案

30:70等はTask件数比ではなく概算総負荷として扱う。

## 人間の実行指示とPlan継続

初回dispatchでは、現在のuser messageに明確な実行指示を要求する。`@excellent-nd` は任意の明示記法として扱い、特別な承認フレーズを追加要求しない。

複数Taskを含むPlan全体への実行指示では、各Task metadataを `dispatch_scope: "plan"` / `human_gate: "clear"` としてDurable化する。単発Task、段階ごとの確認をユーザーが要求したTask、既存legacy Taskは `dispatch_scope: "task"` とする。

`dispatch_scope: "plan"` の後続Taskは、次にChatGPTがPlanをreconcileする機会に以下を全て満たせば、新しい `@excellent-nd` やIssue単位の人間指示なしでroutingしてよい。

- 同じ `plan_ref` の事前定義Taskである
- metadataの `human_gate` が `clear` である
- Durable dependencyが全てterminal / closedである
- repository-native dispatch gatesが全てPASSする
- execution target、scope、acceptance criteriaに未承認変更がない
- routing競合やUNKNOWNがない

この継続はChatGPTのPlan reconciliationで行い、独自schedulerやChatへのbackground pushを追加しない。Skillの自動選択だけで新しいPlanや未計画Taskを開始しない。

Task Issueには:

- Objective
- Constraints
- Acceptance criteria
- Dependencies / owner
- relevant decisions / references
- `references/task-schema.md` のmachine-readable block

を含める。

routing/status表現を固定値で仮定せず、対象repositoryの `.excellent-nd/repository.json` を読む。`dispatch_gates[]` に定義されたrepository固有条件をfail-closed評価し、特定のField名（Status / Agent / Human Approval等）をCore要件として仮定しない。routing labelだけで開始許可と判断しない。

## Execute

通常Taskはrepository configで定義されたrouting labelとtarget-specific labelの両方を持ち、設定済みのgeneric dispatch gatesがすべてPASSした場合だけ対象hostへdispatchする。repository-native DoR / dependency / lock / claimは置換しない。必要データ取得不能・paginationで完全性を証明できない・Project item 0件/複数件・UNKNOWNはSTOPとする。

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

最初のhostにSymphonyがなく通常経路を利用できない場合、人間がChatで明確にbootstrap実行を指示した後にbootstrap Issueを作成し、対象host上で人間がCodex CLI等から明示的に開始する。`@excellent-nd` は任意の明示記法である。

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
- 人間判断が必要なblockedでは `human_gate: "required"` とし、人間回答が得られるまで自動継続しない
- 人間回答そのものを新しい実行指示として扱い、`human_gate: "clear"` へ戻す。Issue番号や特別な承認フレーズを要求しない
- 外部要因によるblockedで `dispatch_scope: "plan"` / `human_gate: "clear"` を維持できる場合は、条件解消を検証した後のPlan reconciliationで継続してよい
- `dispatch_scope: "task"`、scope変更、acceptance criteria変更、execution target変更は新しい人間実行指示を要求する
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
5. terminalになったTaskの後続を確認し、Plan継続条件を満たすTaskがあれば同じturnでfresh preflightしてroutingする。人間へIssue番号やExcellent-Nd内部操作を要求しない
6. 必要がなければraw log全文を取り込まない

## Checkpoint

- branch / commit / diff: code state
- PR: review state
- Issue Workpad: decisions / verification / remaining work / blocker / handoff

## References

- repository onboarding: `references/repository-onboarding.md`
- Task schema: `references/task-schema.md`
- workflow states: `references/workflow.md`
- generic repository mapping / dispatch gates: `references/repository-onboarding.md`
- execution target inventory: `references/execution-targets.md`
- version policy: `references/version-policy.md`
