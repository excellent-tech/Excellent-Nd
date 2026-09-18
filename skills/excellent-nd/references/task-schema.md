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

SymphonyのpromptはIssue body由来の `issue.description` を利用できるため、Objective等の説明情報をJSONへ重複コピーしない。

## 参照規則

- `plan_ref` はrepository内で衝突しない `P-YYYYMMDD-<6文字の小文字16進数>` を推奨し、Issue作成前に同じ値がないことを検索する。
- `task_ref` はPlan内で一意な `T-001` 形式の連番とする。
- 相関keyは `plan_ref` と `task_ref` の組とする。
- Durable Taskの実体参照はGitHub Issue URL / numberとし、元Plan側にも保存する。
- dependencyはGitHub Issue URL、または `plan_ref` と `task_ref` の組で参照する。

中央ID基盤を作らず、repository内検索とGitHub IssueのidentityでV1の結果取り込みに必要な相関を満たす。

## Task control / correlation metadata

このJSONはExecution Packet全体でもCodex向けpromptでもない。routing、状態表示、相関、引継ぎに必要な安定keyだけを持つ。

```json
{
  "schema": "excellent-nd/task@v1",
  "plan_ref": "P-20260918-a1b2c3",
  "task_ref": "T-001",
  "owner": "owner-a",
  "execution_target": "target-a",
  "workflow_status": "scheduled",
  "dependencies": [],
  "supersedes": null,
  "thread_policy": "reuse-for-same-task"
}
```

V1の `workflow_status`:

- `scheduled` = 実行予定
- `running` = 処理中
- `blocked` = 保留
- `review` = レビュー

完了はrepository workflowのterminal Issue stateで表現する。通常はreview / merge方針を満たした後にIssueをcloseする。

## Host移行

1 Issue内の `execution_target` は変更しない。

別targetへ移す場合:

1. 旧Issueにcheckpointを保存する。
2. 新しい `execution_target` を持つ後継Issueを作成する。
3. 後継Issueの `supersedes` に旧Issue参照を設定する。
4. 旧Issueから後継Issueを参照し、旧Issueのroutingを停止する。

同じIssueに複数execution targetの履歴を混在させない。
