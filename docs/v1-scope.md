# 1.0.x スコープ

## 1.0.x の目的

1.0.x は、ChatGPT を主 UI としながら、内部では GitHub Issue + Symphony + Codex を利用して、1 つの Plan から 1 件以上の Task を安全に並列実行できることを確認する。

中心フロー:

> ChatGPT で Plan 作成 → Task 分割・担当配分 → 人間による実行承認（Human GO） → Task ごとに GitHub Issue 作成 → Symphony / Codex 実行 → GitHub に結果保存 → 人間が「結果を取り込んで」→ ChatGPT が元 Plan に再統合

この通常経路を成立させる前提として、Symphony未導入hostでは人間による実行承認（Human GO）済みのbootstrap TaskをGitHub Issueへ記録し、人間が対象host上のCodex CLI等から明示的に開始する限定経路を使う。

新しい管理基盤を作るのではなく、既存の公式機能と オープンソース を組み合わせ、人間の管理作業と AI 間の不要な context 転送を減らすことが目的である。

## 1.0.x 対象

### ChatGPT / Plan

- ChatGPT を要求整理、Plan、GO、結果確認、blocked 確認、次の判断の主 UI とする。
- 1 ChatGPT Chat から 1..N Task を生成できる。
- 1 人作業では 1 Chat → 1 Task になるケースを自然に扱う。
- 複数人作業では 1 Chat → 複数 Task → 複数 Codex thread に分岐できる。

### Task 分割・担当配分

- 人間による実行承認（Human GO） 前に Task 一覧と担当割当を確認できる。
- 「担当A:担当B = 約3:7」等、おおよその作業負荷比率を指定できる。
- 比率は Task 件数ではなく、想定作業量を基準に解釈する。
- 依存関係と並列実行可否を考慮する。
- 高度な最適化ではなく、ChatGPT が合理的な案を作り、人間が GO で確定する。

### Task / Issue

- 1.0.x で実行する Task は GitHub Issue として Durable 化する。
- Taskごとに Plan reference / Task reference / owner / Execution Packet を記録する。
- 通常Taskには利用するprofileのrouting情報を追加する。
- `plan_ref` はrepository内で衝突しない `P-YYYYMMDD-<6文字の小文字16進数>`、`task_ref` はPlan内で一意な `T-001` 形式を基本とし、GitHub Issue URL / numberをDurable Taskの実体参照にする。
- GitHub 操作は ChatGPT の公式連携を優先する。
- 専用 Task DB は作らない。

### Symphony / Codex

- Symphony の GitHub Issues adapter を利用する。
- Symphony に Issue polling、workspace、retry、concurrency、Codex App Server、thread / turn 管理を委ねる。
- 原則 1 Task = 1 Codex thread。
- 同じ Task の修正・review対応は同一 thread 継続を優先する。
- 複数 Task は独立 thread で並列実行可能とする。

### Bootstrap prerequisite

- 最初のexecution hostへのSymphony runtime導入は、通常Taskの前提を作るbootstrap Taskとして区別する。
- 人間による実行承認（Human GO）前には開始しない。開始前にobjective、constraints、acceptance criteria、execution target、verification方法をGitHub Issueへ記録し、完了後にverification結果を追記する。
- Symphony未導入の間だけ、人間が対象host上のCodex CLI等から明示的に開始できる。
- 通常Task用routing label / fieldは要求せず、execution-control条件を付けない。既存profileがある場合もbootstrap Issueをdispatch対象にしない。
- 完了条件はSymphonyの導入とversion、Codex App Server利用可能性、Git / GitHub接続、WORKFLOW / profile読込、routingの非誤dispatch、version set / verification結果の記録までとする。
- runtime / profileのsmoke verification後は、bootstrapのacceptance criteriaに含めず、別の通常Taskでsingle Task E2Eを行う。
- 2台目以降も既存経路でprovisioningできないhostに限り同じ規約を使う。
- bootstrap例外を一般的なmanual executionへ拡大せず、自動provisioning機構も作らない。

### 複数実行 host

- 最初は 1 台の execution host で end-to-end を検証する。
- 問題なく運用できることを確認後、2 台目へ展開する。
- human assignee と execution target は分離して扱う。
- execution targetは管理範囲で一意なhost hostnameを基本とし、public repositoryでは必要に応じnon-sensitive hostname / public aliasを使う。
- Task 作成時に execution target を固定し、同じ Issue の途中では変更しない。
- host 移行が必要な場合は checkpoint を残して後継 Issue を作る。
- routing は Symphony の required labels 等の既存機能を優先する。
- 独自 scheduler / distributed lock は作らない。

### Workflow state

- 実行予定 / `scheduled`
- 処理中 / `running`
- 保留 / `blocked`
- レビュー / `review`

`workflow_status` は人間向け論理状態であり、Symphony実行制御の正本ではない。GitHub native state、adapterのdispatchability、profileのrouting / execution-control label `symphony-ready` を実行制御の正本とする。`nd-status:scheduled|running|blocked|review|failed` は可視化用とする。blocked時は論理状態とcontrol条件の両方を更新し、execution-target identityは維持する。

### Execution Packet

Execution PacketはGitHub Issue body全体とする。実行内容は人間向けMarkdownに記録し、Task control / correlation metadataのJSON blockを併記する。

最低限:

- plan_ref
- task_ref
- owner
- objective
- constraints
- acceptance criteria
- relevant decisions
- relevant references
- dependencies

会話履歴全文を渡さない。

JSONへobjective等を重複コピーしない。runtime / profileは、initial Codex turnのrendered promptへIssue body由来の `issue.description` を必ず含める。非空のcustom `WORKFLOW.md` promptでも `{{ issue.description }}` または同等の方法でExecution Packet全体をrenderし、titleだけを渡す構成を許可しない。

### Execution Result

最低限:

- plan_ref
- task_ref
- status
- summary
- changed files
- diff summary
- verification
- risks
- blockers
- remaining work
- commit / PR / Issue references

Git / test / diff / exit status 等は元データを優先する。

### 結果取り込み

- Codex / Symphony は GitHub Issue / PR に結果を残す。
- ChatGPT への自動 push は行わない。
- 人間が元 Chat で「結果を取り込んで」「状況確認して」等と指示する。
- ChatGPT は複数 Task の結果を取得し、担当別・Task別・Plan全体の状態に再統合する。

### 人間判断ゲート（Human Gate）

- blocked の理由・質問を GitHub に永続化する。
- ChatGPT が人間へ判断事項を提示する。
- 人間の回答を ChatGPT が GitHub に反映し、Task 継続へつなげる。
- 複雑な approval engine は作らない。

### checkpoint / 再開

- Issue Workpad + branch / commit + PR を 1.0.x checkpoint とする。
- 同一 Task は原則同一 Codex thread を継続する。
- 明示的な thread 分割、context 限界、resume 不能、host 移行時は Git + checkpoint から新 thread へ引き継ぐ。
- Codex thread そのものの移送には依存しない。

### Usage limit

- ChatGPT ログイン中アカウントの Codex 利用枠を前提とする。
- 数時間・週次枠の枯渇を短周期 retry し続けない。
- reset timestamp に基づく安全な既存再開手段がなければ Task を保留し、人間の再開指示を利用する。
- 独自 quota-aware scheduler は 1.0.x では作らない。

### ChatGPT Skill

- 共通 workflow を `skills/excellent-nd/` で管理する。
- Plan 分割、GO、Issue 作成、schema、結果取り込み、人間判断ゲート（Human Gate）、host migration の再現性を Skill で確保する。
- 組織固有情報は共通 Skill に含めない。

### Version management

- validated stable と development を分離する。
- validated stable は動作確認済み version set を固定し、latest stable へ自動追従しない。
- バージョン番号と現在の候補版は `skills/excellent-nd/references/version-policy.md` を正本とする。
- 強制アップデートは 1.0.x 全回帰テスト後にのみ stable へ昇格する。

## 1.0.x 非対象

- Issue を使わない lightweight Task の直接実行
- bootstrap例外を一般化したmanual execution
- execution hostの自動provisioning
- lightweight / Durable の自動分類
- Task の完全自動最適配分
- 担当者の能力評価・過去実績学習
- 動的な再配分 / work stealing
- 独自 quota / usage aware scheduling
- ChatGPT への自動 push
- 既存 Chat への外部イベント直接書込み
- 独自 notification infrastructure
- Symphony fork / 再実装
- 独自 Codex Runner / agent harness / App Server client
- 独自 scheduler / retry / workspace manager
- 独自 DB / SQLite
- 独自 GitHub API client
- 独自 Kanban / 大型 Web UI / Project 管理
- multi-agent orchestration
- 複数 AI provider
- Backlog / Jira 等の追加 tracker
- SaaS / multi-tenant
- 大規模チーム向け resource scheduler
- 汎用 workflow engine

## 成功条件

1. ChatGPT 上で 1 つの Plan を作成し、人間による実行承認（Human GO） できる。
2. Plan から 1..N Task を生成できる。
3. 複数 Task を複数担当へ概算負荷比率で割り当てられる。
4. GO 後、Task ごとに GitHub Issue を作成できる。
5. Symphony が対象 Issue を取得し、Task ごとに独立した Codex thread で実行できる。
6. 複数 Task を並列実行できる。
7. Execution Packet全体がinitial Codex turnへ渡り、Codexが必要な作業を進められる。
8. Git / test / diff / PR 等の結果を GitHub に永続化できる。
9. 人間の「結果を取り込んで」という一操作で、ChatGPT が複数 Task の結果を元 Plan に再統合できる。
10. blocked 時に 人間判断ゲート（Human Gate） へ戻り、判断後に同じ Task を継続できる。
11. 1 台目の execution host で end-to-end が安定動作する。
12. 同じ構成を 2 台目へ展開できる見通しが立つ。
13. 共通 ChatGPT Skill により Plan → GO → Issue → Result 取り込みの再現性を確保できる。
14. validated stable / development を分けて version を管理できる。
15. 独自 Runner、独自 DB、独自 scheduler、通知基盤を作らずに上記を満たす。
16. bootstrap Taskを人間による実行承認（Human GO）とIssue記録の下で完了し、その後は通常のSymphony経路だけで実行Taskを処理できる。

## 初期検証順序

1. 人間による実行承認（Human GO）後、1台目のbootstrap Task Issueを作成する。
2. 対象host上のCodex CLI等からbootstrapを明示的に開始し、Symphony stable releaseを導入する。
3. Codex App Server利用可能性、Git / GitHub接続、WORKFLOW / profile読込、routing条件が既存Issueを意図せずdispatchしないことを確認し、version setとverificationをbootstrap Issueへ保存する。
4. routing条件を持つ別の通常Taskで、GitHub Issue → Symphony → Codex → branch / change → verification → PR / Result のsingle Task E2Eを通す。
5. ChatGPT で Plan 作成 → 人間による実行承認（Human GO） → Issue 作成 → 実行開始を確認する。
6. 元 Chat から「結果を取り込んで」で Result を取得する。
7. 同一 Task の continuation を確認する。
8. 2件以上の Task を並列実行する。
9. Plan から複数 Task を作り、担当・負荷配分を反映する。
10. blocked → 人間判断ゲート（Human Gate） → continuation を確認する。
11. 安定後、2台目を既存経路でprovisioningできるか確認し、できない場合だけ限定bootstrap規約を使う。

検証結果が出るまでは、multi-host routing の細部、人間判断ゲート（Human Gate） の具体的遷移、usage telemetry の必須項目を固定しない。
