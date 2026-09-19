# User Guide

[日本語 (authoritative)](operations.md) | [简体中文](operations.zh-CN.md)

The current beta candidate is `1.0.1`; the first normal single-Task E2E is demonstrated.

## Installation

Prerequisites are ChatGPT with Skills/GitHub integration, minimum repository permissions for Issues/labels/branches/PRs, and an execution host for a validated Symphony/Codex CLI-App Server/Git set. Never publish credentials, tokens, private hostnames, or internal URLs.

1. Install `skills/excellent-nd/`; it enables ChatGPT-side rules, not the runtime. 2. Prepare GitHub auth and keep secrets in a secret store. 3. Install upstream Symphony/Codex and pin exact validated versions. 4. Configure the GitHub Issues adapter and include `{{ issue.description }}` or equivalent in the WORKFLOW/profile prompt. 5. Require `symphony-ready`, create the labels below, and verify multi-host routing cannot duplicate dispatch. 6. Approval policy, sandbox, and tool schemas are version-dependent; validate the pinned schema. 7. Smoke-test adapter/profile/prompt/filter/App Server/Git-PR permissions/non-dispatch and record versions/results in the Workpad. 8. Run a separate normal `ChatGPT → Issue → Symphony → Codex → branch/verification → PR → Human review` E2E. Bootstrap is a Human-GO, Issue-recorded exception, not normal manual execution.

## Operations / FAQ

Use `@excellent-nd` in a new chat or when Skill selection is unclear; once active it need not prefix every message. Plan-only work is allowed, but never create/route Issues before Human GO. Flow: Plan/split/owner/workload/target → GO → Issue → Symphony → Codex → PR → human review/merge → Result import → close. The complete Issue body is the Execution Packet rendered from `issue.description`.

30:70 means approximate total workload, not Task count. `owner` is accountable for the result; `execution_target` is the host identity. Do not dispatch while target is unknown. Put requirements/priorities/human decisions in Chat, durable decisions/blockers in the Issue Workpad, and line feedback in PR review; copy execution decisions to the Issue. When blocked, save the reason/question and update status/control; after an answer prefer the same Issue/thread. A changed objective or host uses a checkpointed successor. “Pull in results” reads Workpad/PR/verification/Git state. After merge, confirm Result/remaining work before close.

Symphony orchestrates polling/workspaces/retry/threads; Codex performs and verifies repository work. `No queued retries` is not success; inspect Issue status, runtime log, Workpad, commits/diff, verification, and PR.

## execution_target

Default to a hostname unique in the LAN/organizational scope and keep it unchanged for the Issue lifetime; host moves use successor Issues. If a private/internal hostname would leak infrastructure in a public repository, use a non-sensitive hostname/public alias such as `build-public-01` and keep its mapping outside public artifacts. Do not rewrite existing Issue targets.

## Labels

| Label | Color | Description |
| --- | --- | --- |
| `symphony-ready` | `0E8A16` | Routing / execution control; not workflow status |
| `nd-status:scheduled` | `C2E0C6` | Human GO complete; waiting to run |
| `nd-status:running` | `1D76DB` | Codex execution in progress |
| `nd-status:blocked` | `D93F0B` | Waiting for human, external condition, or quota |
| `nd-status:review` | `FBCA04` | Waiting for human review |
| `nd-status:failed` | `B60205` | Cannot continue automatically; inspect the cause |

Create with `gh label create NAME --color HEX --description TEXT`; customize in GitHub UI or `gh label edit OLD --name NEW --color HEX --description TEXT`. Keep one status label active. Synchronize Skill/docs/automation on rename. A `symphony-ready` rename requires every profile's `required_labels` update and a smoke test. Never toggle it merely to display running status. Pre-turn failures may have no automatic actor; update failed/blocked from logs, Workpad, or result ingestion rather than claiming complete automation.

## Versioning

Stable is `X.Y`; beta/development is `X.Y.Z`. `1.0.1` is the first candidate toward `1.0`. PR #7 creates no tag and is not self-merged. After Human merge, tag the main merge commit `1.0.1` as the release gate.

## Uninstall / disable

Disable/delete the Skill; stop Symphony and remove systemd/container/login-item auto-start; retain host-local WORKFLOW/profiles for rollback or safely delete them; stop routing-label use and optionally clean labels after profiles stop; revoke GitHub/Codex credentials/tokens at the provider and remove host copies without recording values; optionally clean workspaces/caches/logs after audit/recovery checks; normally retain Issues/PRs/commits/history as audit records. Uninstalling Excellent-Nd does not delete Codex or GitHub.
