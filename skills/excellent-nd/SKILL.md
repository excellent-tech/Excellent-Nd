---
name: excellent-nd
description: "Use when ChatGPT manages the Excellent-Nd conversation-first Plan-and-Execute workflow: turn a ChatGPT Plan into one or more GitHub-backed execution Tasks after explicit Human GO, allocate owners and approximate workload, create or update human-readable plus machine-readable Task Issues, pull Issue/PR/test results back into the originating Plan, and handle blocked, review, continuation, host routing, and handoff rules. Use only generic/public workflow rules; keep organization-specific project names, hosts, credentials, and private operating details outside this skill."
---

# Excellent-Nd

Operate ChatGPT as the planning and decision UI while using GitHub Issues as durable Task envelopes and Symphony/Codex as the execution path.

## Core rules

1. Do not start executable work before explicit Human GO.
2. Treat one ChatGPT chat as a planning context that may produce 1..N Tasks.
3. Treat each executable Task as one GitHub Issue in V1.
4. Prefer one Codex thread per Task. Reuse that thread for continuation of the same Task when available.
5. Create a new thread when the user explicitly requests separation, the execution context is no longer reliable, or continuation cannot be resumed. Carry forward Git state plus checkpoint data instead of full conversation history.
6. Keep `owner` and `execution_target` separate.
7. Fix `execution_target` for the lifetime of an Issue. If work must move to another host, create a successor Issue and link the old and new Issues; do not rewrite the same Issue to another host.
8. Do not push execution results into a ChatGPT conversation automatically. When the user asks to import or check results, pull GitHub Issue/PR/verification data and merge it back into the Plan context.
9. Prefer existing ChatGPT/GitHub/Symphony capabilities over a custom runner, database, scheduler, notification service, or App Server client.
10. Never place private project names, internal host names, credentials, tokens, or organization-specific operating details in this public/common skill.

## Workflow

### 1. Plan

Help the user create a Plan and identify executable Tasks. Before GO, show the proposed Task split, dependencies, owner allocation, and approximate workload distribution.

When the user gives a ratio such as 30:70, interpret it as approximate total workload rather than a strict Task-count ratio. Consider dependencies, parallelizability, and estimated effort.

### 2. Human GO

Only after explicit GO, create or update the executable GitHub Issues. Each Issue must contain:

- a human-readable Task description;
- acceptance criteria and relevant constraints;
- dependencies and owner;
- a machine-readable block following `references/task-schema.md`;
- execution routing labels or fields required by the active Symphony profile.

Use the workflow states defined in `references/workflow.md`.

### 3. Execute

Route the Issue to its fixed `execution_target`. Let Symphony own polling, workspace lifecycle, retry for transient failures, Codex App Server launch, thread/turn handling, continuation, and concurrency.

Do not treat ordinary transient retry policy as a quota-exhaustion strategy. If an account usage window is exhausted, follow the rate-limit handling in `references/workflow.md`.

### 4. Blocked / Human Gate

When execution requires human judgment:

- set the Task to blocked/保留;
- persist the reason, evidence, and exact question in the Issue workpad;
- stop executable routing for that Issue;
- present the decision to the user when they ask for status/results;
- after the user answers, record the decision and make the same Issue executable again;
- prefer continuation of the same Codex thread.

### 5. Review

Use the Issue as the Task workpad and state record. Use the PR as the code-change and review artifact. A Task in review/レビュー should have a PR or equivalent reviewable change reference and verification results.

### 6. Import results

When the user says things such as “結果を取り込んで”, “状況確認して”, or asks for Task/owner progress:

1. Identify the Plan and its Task Issues.
2. Read each Issue workpad and linked PR.
3. Retrieve verification/test status and relevant Git facts.
4. Summarize by Task and owner.
5. Reconstruct the Plan-wide status, blockers, risks, and next decisions.
6. Do not import full raw logs unless the user specifically needs them.

## Checkpoint policy

Use these as the V1 checkpoint:

- Git branch / commits / diff for code state;
- PR for reviewable change state;
- Issue workpad for decisions, completed work, verification, remaining work, blockers, and handoff information.

Do not require a separate repository artifact or custom database in V1.

## Version policy

Treat the execution stack as a validated version set rather than automatically following latest versions. See `references/version-policy.md`.
