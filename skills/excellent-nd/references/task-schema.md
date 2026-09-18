# Task Issue schema

Each executable Issue must remain readable to a human and also include a machine-readable JSON block for Codex-oriented automation.

## Human-readable section

Include, at minimum:

- Task title and purpose
- Owner
- Objective
- Constraints
- Acceptance criteria
- Dependencies
- Relevant decisions/references
- Current status

## Machine-readable block

Use a fenced JSON block. Keep keys stable within schema v1.

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

Allowed `workflow_status` values for V1:

- `scheduled` = 実行予定
- `running` = 処理中
- `blocked` = 保留
- `review` = レビュー

Completion is represented by the repository workflow's terminal Issue state, normally a closed Issue after review/merge policy is satisfied.

## Host migration

`execution_target` is immutable for one Issue. To move execution to another target:

1. Persist a checkpoint in the old Issue.
2. Create a successor Issue with a new `execution_target`.
3. Set `supersedes` in the successor to the old Issue reference.
4. Link the old Issue to the successor and stop routing the old Issue.

Do not mix multiple execution-target histories into the same Issue.
