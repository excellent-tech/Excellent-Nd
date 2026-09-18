# Workflow conventions

## Human-facing states

Use these four active workflow states:

| Human label | Machine value | Meaning |
| --- | --- | --- |
| 実行予定 | `scheduled` | GO済みで実行可能 |
| 処理中 | `running` | Codexが処理中 |
| 保留 | `blocked` | 人間判断、外部条件、利用枠等で停止 |
| レビュー | `review` | 実装・検証が終わりレビュー待ち |

Keep display status separate from execution-control labels. A profile may use labels such as an execute/ready label and one routing label per execution target.

## Continuation

For the same Task, prefer the same Codex thread when continuation is available.

Start a new thread only when one of these applies:

- the user explicitly requests a separate thread;
- the context has become unreliable or too large;
- the thread cannot be resumed;
- work is migrated to a new execution target and successor Issue;
- the Task objective has materially changed enough to become a new Task.

Carry forward Git state and the Issue checkpoint, not the full prior chat transcript.

## Blocked and resume

When blocked by a human decision:

1. Persist the reason and exact question in the Issue workpad.
2. Set state to `blocked` / 保留.
3. Remove or disable the execution-control condition so Symphony does not continue the Issue.
4. Keep the execution-target routing identity unchanged.
5. After the human answer is recorded, set state to `scheduled` / 実行予定 and re-enable execution.
6. Prefer continuation of the same Task thread.

## Account usage / rate-limit exhaustion

Do not use a short transient retry loop as the primary response to a multi-hour or weekly account usage limit.

If a reliable reset timestamp is available:

- persist the usage-limit reason and reset timestamp in the Issue workpad;
- set the Task to `blocked` / 保留;
- resume at or after the reset time only through a supported scheduling mechanism.

If a reliable reset timestamp or safe scheduler is not available:

- persist the usage-limit condition;
- keep the Task blocked;
- let a human explicitly request resume later.

Do not add a custom quota-aware scheduler in V1. Revisit only if manual resume or existing scheduling becomes operationally costly.
