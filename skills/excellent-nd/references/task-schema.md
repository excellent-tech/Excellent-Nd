# Task Issue schema

実行対象Issueのbody全体をExecution Packetとする。人間が読めるMarkdownに実行内容を記録し、Excellent-Ndが安定して扱うTask control / correlation metadataをJSON blockで併記する。

## 人間向けセクション

最低限、次を含める。

- Task名と目的
- Owner
- Objective
- Constraints
- Acceptance criteria
- Dependencies
- Relevant decisions / references
- Current status

## Prompt伝達要件

GitHub Issues adapterはIssue bodyを `issue.description` として正規化する。Excellent-Ndのruntime / profileは、initial Codex turnのrendered promptへこの値を必ず含める。

Symphony v0.0.3のdefault promptは `issue.description` を含むが、非空のcustom `WORKFLOW.md` promptはdefault promptを置き換える。custom promptでも `{{ issue.description }}` または同等の方法でExecution Packet全体をrenderし、titleだけを渡してIssue bodyを失う構成を許可しない。

この要件によりIssue body全体がCodexへ渡るため、Objective等の説明情報をJSONへ重複コピーしない。

## Dispatch gate

通常Taskのrouting labelを追加・復元する時点のuser messageに、case-insensitiveな `@excellent-nd` と人間による実行承認（Human GO）の両方を要求する。Task metadataや過去messageだけでは許可しない。dispatchableにする時は対象repositoryの `.excellent-nd/repository.json` で定義されたrouting labelと、同configのtarget prefixから導出したtarget labelの両方を要求する。`review` / `blocked`では同じIssue更新でconfigured routing labelを外し、target labelはcorrelation用に残してよい。label名を固定値として仮定しない。

## 参照規則

- `plan_ref` はrepository内で衝突しない `P-YYYYMMDD-<6文字の小文字16進数>` を推奨し、Issue作成前に同じ値がないことを検索する。
- `task_ref` はPlan内で一意な `T-001` 形式の連番とする。
- 相関keyは `plan_ref` と `task_ref` の組とする。
- Durable Taskの実体参照はGitHub Issue URL / numberとし、元Plan側にも保存する。
- dependencyはGitHub Issue URL、または `plan_ref` と `task_ref` の組で参照する。

中央ID基盤を作らず、repository内検索とGitHub Issueのidentityで1.0.xの結果取り込みに必要な相関を満たす。

## Task control / correlation metadata

このJSONはExecution Packet全体でもCodex向けpromptでもない。routing、状態表示、相関、引継ぎに必要な安定keyだけを持つ。

```json
{
  "schema": "excellent-nd/task@v1",
  "plan_ref": "P-20260918-a1b2c3",
  "task_ref": "T-001",
  "owner": "owner-a",
  "execution_target": "build-public-01",
  "workflow_status": "scheduled",
  "dependencies": [],
  "supersedes": null,
  "thread_policy": "reuse-for-same-task"
}
```

1.0.xの `workflow_status`:

- `scheduled` = 実行予定
- `running` = 処理中
- `blocked` = 保留
- `review` = レビュー

完了はrepository workflowのterminal Issue stateで表現する。通常はreview / merge方針を満たした後にIssueをcloseする。

## execution_target identity / Host移行

基本identityは同一LAN / 組織管理範囲で一意なhost hostnameとする。public repositoryでprivate/internal hostnameがinfra情報を漏らす場合はnon-sensitive hostname / public aliasを使い、mappingは公開artifact外に保持する。


1 Issue内の `execution_target` は変更しない。

別targetへ移す場合:

1. 旧Issueにcheckpointを保存する。
2. 新しい `execution_target` を持つ後継Issueを作成する。
3. 後継Issueの `supersedes` に旧Issue参照を設定する。
4. 旧Issueから後継Issueを参照し、旧Issueのroutingを停止する。

同じIssueに複数execution targetの履歴を混在させない。
