# Excellent-Nd 設計

本書は Excellent-Nd の設計判断の正本である。Symphony に関する事実は 2026-09-18 時点の OpenAI 公式リポジトリ `be10a1b79df723d6d7612b5651c8522704dafb2e` を確認した。未確定事項は [open-questions.md](open-questions.md) に分離する。

## 背景と課題

ChatGPT 上の相談は、要求整理、選択肢比較、Plan 作成、人間判断を一つの会話文脈で進めやすい。一方、小人数開発で人間がすべての作業を手作業で Issue 化・更新すると、管理自体が負担になりうる。

Excellent-Nd は、人間に Issue 管理を強いるのではなく、ChatGPT を主 UI としながら、実行時の Durable Task は GitHub Issue と Symphony に委ねる。

V1 では「Issue を使わない実行経路」を新たに作らない。人間から見た UX は Conversation-first、内部実行は Issue-first とすることで、独自 Runner や独自状態管理を増やさずに成立するかを検証する。

## 目的

Excellent-Nd は、ChatGPT 上の 1 つの Plan から 1 件以上の Task を切り出し、人間の GO 後に担当・依存関係・おおよその負荷配分を反映して GitHub Issue 化し、Symphony / Codex で実行する。

実行結果は GitHub に永続化し、人間が元の ChatGPT 会話で「結果を取り込んで」「状況を確認して」等と明示したときに、ChatGPT が各 Task の結果を取得して元 Plan へ再統合する。

## 設計原則

1. ChatGPT を要求整理、Plan、担当分割、GO、結果確認、次の判断の主 UI とする。
2. Human GO 前に実行しない。
3. 1 ChatGPT Chat は 1 つの計画・判断コンテキストとして扱い、そこから 1 件以上の Task に分岐できる。
4. 実行コンテキストは Task 単位とし、原則として 1 Task = 1 Codex thread とする。
5. 同じ Task の追加修正、test failure 修正、review 対応は同一 thread の継続を優先する。
6. V1 の通常実行 Task は GitHub Issue として Durable 化し、Symphony の Issue-first orchestration を利用する。
7. 全会話ではなく、Task ごとに必要な Execution Packet のみを実行側へ渡す。
8. Codex の生ログ全文ではなく、Git / test / diff 等の機械情報と短い要約からなる Execution Result を戻す。
9. GitHub 操作は ChatGPT の公式連携と Symphony の既存 integration を優先する。
10. Symphony と Codex が持つ scheduler / runner / workspace / retry / thread 管理を再実装しない。
11. ChatGPT への自動 push は V1 では行わず、人間の明示的な結果取り込みを基本とする。
12. 管理画面や状態を増やすより、人間が管理する情報量を減らす。
13. Symphony runtime の bootstrap prerequisite は通常実行 Task と区別し、Human GO とGitHub上の永続記録を維持した限定例外とする。

## V1 の全体モデル

```text
Human
  ↓
ChatGPT Chat
  - 要求整理
  - Plan
  - Task分割
  - 担当 / 負荷配分
  - Human GO
  ↓
GitHub Issues
  - Plan参照
  - Task参照
  - 担当
  - routing
  - Execution Packet
  ↓
Symphony
  ↓
Codex thread per Task
  ↓
Git / Test / PR / Issue Result
  ↓
GitHub
  ↓
Human: 「結果を取り込んで」
  ↓
ChatGPT
  - 複数TaskのResult取得
  - 元Planへ再統合
  - 次の判断
```

## Chat / Plan / Task / Codex thread の関係

### ChatGPT Chat

人間との計画・判断の文脈である。1 Chat 内で複数 Task を扱ってよい。

### Plan

Chat 内で合意した作業計画である。必要に応じ複数 Task に分割する。

V1 では Plan を独立 DB に保存しない。元 Chat と、GitHub Issue に記録する Plan 参照で相関できればよい。

### Task

Codex に渡す独立した実行目的である。

1 つの Plan から 1..N Task を生成できる。

例:

```text
Plan P-20260918-a1b2c3
├─ T-001: 担当A
├─ T-002: 担当A
├─ T-003: 担当B
└─ T-004: 担当B
```

### Codex thread

Task を実行する AI 文脈である。

- 原則: 1 Task = 1 thread
- 同一 Task の継続: 同一 thread を優先
- 別 Task: 別 thread
- thread を再利用できない場合: Git + checkpoint から新規 thread で再開

Chat ID と Codex thread ID を 1:1 で固定しない。

`plan_ref` はrepository内で衝突しない `P-YYYYMMDD-<6文字の小文字16進数>` を推奨し、Issue作成前に検索する。`task_ref` はPlan内で一意な `T-001` 形式とし、両者の組を相関keyにする。Durable TaskそのものはGitHub Issue URL / numberで識別し、元Planにもその参照を保存する。日付と短いrandom tokenにrepository内検索を組み合わせれば、中央ID基盤なしでV1の相関に十分である。

## 複数 Task と担当配分

V1 では、ユーザーが 1 つの Plan 内で複数 Task の一括実行を指示できる。

例:

> Task 1〜10 を担当Aと担当Bに、おおよそ 3:7 の負荷で分けて進める。

ChatGPT は次を考慮して Task を割り当てる。

- 想定作業量
- Task 間の依存関係
- 並列実行可否
- ユーザーが指定した担当
- ユーザーが指定した概算負荷比率

3:7 等の比率は Task 件数の厳密比率ではなく、**おおよその総作業負荷**として解釈する。

V1 では高度な最適化 scheduler は作らない。ChatGPT が合理的な割当案を作り、人間が GO することで確定する。

## Human GO と一括 Issue 作成

Human GO 後、ChatGPT は実行対象 Task ごとに GitHub Issue を作成または更新する。

Issue には最低限、次を相関可能な形で記録する。

- Plan reference
- Task reference
- assignee / owner
- execution target
- 通常Taskのrouting information
- objective
- constraints
- acceptance criteria
- relevant decisions
- relevant references
- dependencies

V1 では専用 DB を作らない。

## Bootstrap prerequisite

通常の実行経路は Human GO → GitHub Issue → Symphony → Codex である。ただし最初のexecution hostにはSymphony runtimeが存在しないため、Symphony自身の導入を同じ経路から開始できない。

この循環依存を避けるため、runtime readinessとsmoke verificationを確認するbootstrap Taskだけは次の限定規約を使う。

1. ChatGPT上でPlanとbootstrap Taskを作り、通常と同じHuman GOを得る。
2. GitHub Issueにobjective、constraints、acceptance criteria、execution target、verification方法を永続化する。
3. 利用可能なSymphony profileはまだ存在しないため、通常Task用routing label / fieldは要求せず、execution-control条件を付けない。既存profileがある場合もbootstrap Issueを選択できない状態にする。
4. 人間が対象host上のCodex CLI等から、そのIssueを作業記録として明示的に開始する。
5. Symphonyの導入とversion、Codex App Server利用可能性、Git / GitHub接続、WORKFLOW / profile読込、routing条件が既存Issueを意図せずdispatchしないことを確認する。
6. 実測したversion setとverification結果をIssueへ記録し、bootstrapを完了する。

bootstrap完了後、routing条件を持つ別の通常Task Issueで `GitHub Issue → Symphony → Codex → branch / change → verification → PR / Result` のsingle Task E2Eを実施する。bootstrapのacceptance criteriaにこのE2Eを含めない。

bootstrapは通常Taskのmanual execution経路ではない。2台目以降も既存のExcellent-Nd / Symphony経路でhost provisioningできない場合に限り同じ規約を使う。V1では自動provisioning機構を作らない。

## 実行 host と routing

V1 はまず 1 台の execution host で end-to-end を検証し、安定後に 2 台目へ展開する。

人間の責任者である `owner / assignee` と、実際に Codex を動かす `execution_target` は分離する。

`execution_target` は管理範囲で一意なhost hostnameを基本とし、public repositoryでは必要に応じnon-sensitive hostname / public aliasを使う。Task 作成時に `execution_target` を決定し、**1 Issue の lifetime 中は固定する**。明示的な host 移行が必要になった場合は、同じ Issue の host 情報を書き換えず、checkpoint を残して後継 Issue を作成する。これにより 1 Issue 内に複数 host の実行履歴を混在させない。

複数 host では Symphony の `required_labels` 等を使って host ごとに routing 条件を分離し、同じ Issue を複数 instance が取得しない構成を優先する。独自分散 scheduler / lock は V1 では追加しない。

## Symphony の責務

[Symphony README](https://github.com/openai/symphony/blob/be10a1b79df723d6d7612b5651c8522704dafb2e/README.md)、[SPEC.md](https://github.com/openai/symphony/blob/be10a1b79df723d6d7612b5651c8522704dafb2e/SPEC.md)、[Elixir implementation README](https://github.com/openai/symphony/blob/be10a1b79df723d6d7612b5651c8522704dafb2e/elixir/README.md) と同revisionの実装から、V1 では次を Symphony に委ねる。

- Issue tracker polling
- dispatch / claim
- per-Issue workspace
- Codex App Server 起動
- thread / turn 管理
- continuation
- retry / backoff
- concurrency
- reconciliation
- runtime observability
- 取得可能な usage / rate-limit telemetry
- tracker integration

Excellent-Nd はこれらを複製しない。

現行Elixir実装のGitHub Issues adapterはIssue bodyを `issue.description` に正規化する。Symphony v0.0.3のdefault promptはこの値を含み、非空のcustom `WORKFLOW.md` promptはdefault promptを置き換える。dispatchとcontinuationは、GitHub native state、adapterのdispatchability、設定された全 `required_labels` の一致を使って判定する。

## Codex App Server

Codex App Server は Symphony 固有機能ではなく、Codex を外部プログラムから制御するための公式インターフェースである。

Symphony は Codex App Server を利用して Task ごとの coding session を管理する。

Excellent-Nd は Codex App Server client を独自実装しない。

## Execution Packet

会話全文ではなく、Task ごとに最低限次を渡す。

| 項目 | 内容 |
| --- | --- |
| `plan_ref` | 元 Plan を識別する参照 |
| `task_ref` | Task を識別する参照 |
| `owner` | 人間側の担当 |
| `objective` | この Task で達成する目的 |
| `constraints` | 禁止事項、範囲、互換性、安全条件 |
| `acceptance_criteria` | 完了条件 |
| `relevant_decisions` | 実行に影響する確定済み判断 |
| `relevant_references` | Issue、文書、ファイル、commit 等 |
| `dependencies` | 先行 Task 等の依存関係 |

V1 では **GitHub Issue body全体をExecution Packet** とする。Objective、Constraints、Acceptance criteria、Relevant decisions / references等は人間が読めるMarkdownへ記録する。

Excellent-Ndのruntime profileには、initial Codex turnのrendered promptへIssue body由来の `issue.description` を必ず含める伝達要件を設ける。custom `WORKFLOW.md` promptでは `{{ issue.description }}` または同等の方法を使い、titleだけを渡してExecution Packetを失う構成を許可しない。

併記するJSON blockはExecution Packet全体でもCodex向け説明でもなく、Excellent-Ndが安定して扱う **Task control / correlation metadata** である。`plan_ref`、`task_ref`、owner、execution target、論理状態等だけを持ち、説明情報を重複コピーしない。初期schemaは `skills/excellent-nd/references/task-schema.md` を正とする。

## Execution Result

Codex / Symphony の結果は GitHub Issue / PR 等へ永続化し、ChatGPT は人間の明示的な取り込み指示時に取得する。

最低限次を扱う。

| 項目 | 内容 |
| --- | --- |
| `plan_ref` | 元 Plan の参照 |
| `task_ref` | Task の参照 |
| `status` | completed / blocked / failed 等 |
| `summary` | 人間判断用の短い要約 |
| `changed_files` | 変更ファイル |
| `diff_summary` | diff 統計・主要変更 |
| `verification` | test / check / exit status |
| `risks` | 既知リスク |
| `blockers` | 人間判断または外部条件待ち |
| `remaining_work` | 未完了範囲 |
| `references` | commit / PR / Issue 等 |

Git、test、diff、exit status 等の機械情報は、可能な限り元データを利用し、LLM に再生成させない。

## 結果の元 Chat への取り込み

V1 では自動 push を行わない。

人間が元 Chat で次のように指示する。

- 「結果を取り込んで」
- 「進行中 Task の状況を確認して」
- 「担当Aと担当Bの結果をまとめて」

ChatGPT は GitHub から Plan に紐づく各 Task / PR / verification を取得し、元 Plan の文脈へ再統合する。

この一操作で十分な間は、既存 Chat への自動書込み IF や独自 notification infrastructure を作らない。

## Workflow state と Human Gate

V1 の人間向け active state は次の 4 つとする。

| 表示 | machine value | 意味 |
| --- | --- | --- |
| 実行予定 | `scheduled` | Human GO 済みで実行可能 |
| 処理中 | `running` | Codex が処理中 |
| 保留 | `blocked` | 人間判断、外部条件、利用枠等で停止 |
| レビュー | `review` | 実装・検証後のレビュー待ち |

`workflow_status` はExcellent-Ndと人間向けの論理状態であり、JSON値だけを変更してもSymphonyの実行は制御されない。

Symphony execution controlの正本はGitHub native state、adapterのdispatchability、profileで設定した `required_labels` を満たすrouting / execution-control labelである。routing labelは `symphony-ready`、可視化用は `nd-status:scheduled|running|blocked|review|failed` とする。

人間判断が必要になったTaskはIssue Workpadにblocked理由・根拠・質問を保存し、`workflow_status` を `blocked` に更新してexecution-control条件を外す。execution-target identityは変更しない。人間回答を保存した後、`workflow_status` を `scheduled` に戻してexecution controlを再度有効化し、原則として同じCodex threadのcontinuationを試みる。

```text
Task → 保留
     → Issue Workpad に質問・根拠
     → ChatGPT で状況取得
     → Human decision
     → Issue に回答を保存
     → 実行予定へ戻す
     → same Task continuation
```

V1 では複雑な approval engine を作らない。

## checkpoint

V1 の checkpoint は **Issue Workpad + branch / commit + PR** を基本とする。

- Git branch / commit / diff: コード状態
- PR: レビュー可能な変更状態
- Issue Workpad: objective、decisions、completed work、remaining work、verification、risks / blockers、handoff

repository artifact や独自 DB は V1 では必須にしない。Codex 会話全文も復旧の正本にしない。

## Account usage limit と再開

通常の一時エラーには Symphony の retry / backoff を利用できるが、数時間の usage window や週次枠の枯渇に短周期 retry を繰り返す運用は採用しない。

usage limit を検出した場合は Task を `blocked` / 保留として Issue Workpad に理由を保存する。信頼できる reset timestamp が取得でき、既存機能で安全に時刻指定再開できる場合は reset 後の再開を利用する。V1 の標準機能だけで安全な長時間再開を構成できない場合は、人間の明示的な再開指示を使用する。

独自 quota-aware scheduler は V1 では作らない。必要性は実運用で再評価する。

## ChatGPT Skill

共通の ChatGPT 操作規約は `skills/excellent-nd/` で管理する。

Skill は新しい通信 IF を提供するものではなく、Plan 分割、Human GO、Issue 作成、Task control / correlation metadata、結果取り込み、Human Gate、host migration 等を ChatGPT が一貫して実行するための再利用可能な workflow である。

組織・プロジェクト固有の host 名、credential、非公開運用ルールは public Skill に含めない。

## Version policy

実行環境は常に latest に追従せず、**validated stable** と **development** を分離する。

validated stable は Symphony / Codex / WORKFLOW / Skill の動作確認済み version set を固定して通常作業に使用する。新しい stable release が出ても自動更新しない。

development は新しい stable / nightly / development version の検証専用とする。

強制アップデート時は、single Task、multi Task、routing、continuation、Human Gate、PR、result import、Task control / correlation metadata、usage limit、restart/recovery を含む V1 全回帰テストを通してから validated stable へ昇格する。

正式版は `X.Y`、beta / development版は `X.Y.Z`、current candidateは `1.0.1`。詳細は `skills/excellent-nd/references/version-policy.md` を参照する。

## トークン削減

- Chat 全履歴を Task prompt にしない。
- Plan から各 Task に必要な情報だけ Execution Packet に切り出す。
- Task A の情報を Task B に不要なら渡さない。
- Codex の全イベント / ログを ChatGPT へ戻さない。
- Result は構造化し、人間の判断に必要な内容だけ ChatGPT で表示する。
- Git / test / diff / exit status 等は機械データを利用する。
- 同一 Task の continuation では thread 継続を優先する。

## V1 で扱わない領域

- Issue を使わない lightweight Task の直接実行経路
- bootstrap例外を一般化したmanual execution経路
- execution hostの自動provisioning
- lightweight / Durable Task の自動分類
- 自動 Task routing 最適化
- 担当者能力や過去実績に基づく自動配分
- リアルタイム負荷再配分
- quota / token 残量を使った自動 scheduling
- ChatGPT への自動 push / 既存 Chat への外部書込み
- 独自 notification daemon / webhook relay
- Symphony fork / 再実装
- 独自 Codex Runner / Codex App Server client
- 独自 scheduler / retry / workspace manager
- 独自 DB / SQLite
- 独自 GitHub API client
- 独自 Kanban / 大型 Web UI
- multi-agent orchestration
- 複数 AI provider
- 複数 tracker
- SaaS / multi-tenant
- 汎用 workflow engine

将来候補は実運用で不足が確認された場合のみ再検討する。
