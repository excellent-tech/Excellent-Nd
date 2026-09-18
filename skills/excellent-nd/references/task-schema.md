# Task Issue schema

実行対象Issueは、人間が読める説明と、Codex向けのmachine-readable JSON blockを両方持つ。

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

## Machine-readable block

fenced JSON blockを使う。schema v1のkeyは安定して扱う。

```json
{
  "schema": "excellent-nd/task@v1",
  "plan_ref": "P-001",
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
