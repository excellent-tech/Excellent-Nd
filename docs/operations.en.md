# User Guide

[日本語 (authoritative)](operations.md) | [简体中文](operations.zh-CN.md)

This guide is for operators installing, running, and disabling Excellent-Nd. See the [version policy](../skills/excellent-nd/references/version-policy.md) for numbering rules and the current candidate.

## Installation

### 1. Check prerequisites

- **Action**: Prepare ChatGPT, a GitHub repository, and an execution host.
- **Command / UI**: Confirm ChatGPT can use Skills and GitHub integration, GitHub can operate Issues, labels, branches, and PRs, and Git is available on the host.
- **Expected result**: Minimum permissions are available and credentials can be stored securely.
- **If OK**: Continue to step 2.
- **If not OK**: Stop until permissions and secret storage are ready. Never publish credentials, tokens, private hostnames, or internal URLs.

### 2. Install the excellent-nd Skill

- **Action**: Install `skills/excellent-nd/` on the ChatGPT side.
- **Command / UI**: Add and enable it in ChatGPT Skill management.
- **Expected result**: `excellent-nd` appears in the Skill list and can be selected.
- **If OK**: Continue to step 3.
- **If not OK**: Check the path, permissions, and metadata. Do not proceed to runtime setup.

> **Illustration candidate 1**: Capture the ChatGPT Skill list with `excellent-nd` selectable. Show the name and enabled state; do not show conversations, tokens, account details, or private URLs.

### 3. Prepare GitHub

- **Action**: Configure the target repository and authentication.
- **Command / UI**: Grant a GitHub App or official integration minimum permissions for Issues, labels, branches, and PRs. Store secrets in the host secret store.
- **Expected result**: A test Issue can be read and written, and required branch and PR operations work.
- **If OK**: Continue to step 4.
- **If not OK**: Correct installation scope, permissions, and repository selection. Do not paste secrets into Issues or logs.

### 4. Prepare Symphony and Codex

- **Action**: Install upstream Symphony and Codex CLI / App Server on the execution host and pin the exact version set under validation.
- **Command / UI**: Follow upstream instructions and record measured versions with their version commands.
- **Expected result**: Symphony and Codex App Server start, and Git and GitHub connectivity works.
- **If OK**: Continue to step 5.
- **If not OK**: Check upstream requirements, permissions, network access, and authentication. Keep Issues non-dispatchable.

> **Illustration candidate 2**: Capture Symphony's healthy state after startup. Show only the running process and intended configuration; do not show tokens, private hostnames, private paths, environment variables, or internal URLs.

### 5. Configure WORKFLOW, profile, and GitHub Issues adapter

- **Action**: Configure the adapter and target-host profile.
- **Command / UI**: Include `{{ issue.description }}` or its equivalent in the initial prompt. Require `symphony-ready` for normal Tasks and ensure multi-host conditions do not overlap.
- **Expected result**: The complete Issue body reaches the initial Codex prompt and non-target Issues are not dispatched.
- **If OK**: Continue to step 6.
- **If not OK**: Correct the WORKFLOW, profile, adapter schema, and label conditions. Never use a title-only prompt.

### 6. Create routing and status labels

- **Action**: Create the labels in [Status labels](#status-labels).
- **Command / UI**: Use the GitHub labels UI or `gh label create`.
- **Expected result**: An approved Issue can carry both `symphony-ready` and `nd-status:scheduled`.
- **If OK**: Continue to step 7.
- **If not OK**: Check label names, permissions, and profile `required_labels`.

> **Illustration candidate 3**: Capture an Issue with both `symphony-ready` and `nd-status:scheduled`. Make both roles visible; do not show secrets, private hostnames, or private URLs.

### 7. Verify version compatibility and run smoke verification

- **Action**: Measure approval policy, sandbox, tool schema, and the complete configuration.
- **Command / UI**: Check adapter connectivity, profile loading, prompt rendering, label filtering, App Server, Git / PR permissions, and non-dispatch of out-of-scope Issues. Record exact versions and results in the Workpad.
- **Expected result**: Every check passes and the record contains no secrets.
- **If OK**: Continue to step 8.
- **If not OK**: Consult the pinned version's schema instead of another version's example. Do not dispatch normal Tasks.

### 8. Run the first single-Task E2E

- **Action**: After Human GO, run a normal Task separate from bootstrap.
- **Command / UI**: Complete `ChatGPT → Issue → Symphony → Codex → branch / verification → PR → Human review` and save results to the Workpad and PR.
- **Expected result**: The full Issue body, changes, verification, PR, and review state are traceable.
- **If OK**: Begin normal operations.
- **If not OK**: Inspect runtime logs, Workpad, Git diff, verification, and PR. Do not dispatch more Tasks until resolved.

Installing the Skill does not install the runtime. Bootstrap on an unprepared host is a limited exception explicitly started by a human after Human GO and Issue persistence; it is not the normal manual execution path.

## Operations / FAQ

### Q. When should I use `@excellent-nd`?

A. Use it in a new conversation or when the Skill is not selected automatically. Once active, it need not prefix every message.

### Q. Can I create only a Plan without routing work?

A. Yes. Define the Plan, Task split, owners, approximate workload, and target candidates. Do not create or dispatch Issues before Human GO.

### Q. What is the normal flow?

A. `ChatGPT → GitHub Issue → Symphony → Codex → PR → Human review → merge → Result import → Issue close`. After merge, confirm the Workpad, verification, and remaining work before closing.

> **Illustration candidate 4**: Capture the Issue, linked PR, and review relationship. Show cross-links and review state; do not show private repository or branch names, or secret-bearing diffs and logs.

### Q. How does the Issue body relate to the Codex prompt?

A. The complete Issue body is the Execution Packet. The adapter normalizes it as `issue.description`, and the WORKFLOW / profile renders it into the initial Codex prompt.

### Q. How are Tasks split and a 30:70 workload assigned?

A. Split 1..N Tasks based on dependencies, parallelizability, and estimated effort. 30:70 means approximate total workload, not Task count.

### Q. What is the difference between `owner` and `execution_target`?

A. `owner` is accountable for the result. `execution_target` identifies the host running Codex. Keep the Issue non-dispatchable while unknown.

### Q. Where should review feedback go?

A. Put requirements, priorities, and human decisions in Chat; durable decisions and blockers in the Workpad; and line-level feedback in PR review. Copy execution decisions to the Issue.

> **Illustration candidate 5**: Capture returning PR feedback to Chat. Show the PR reference, requested change, and same-Task continuation; do not show unrelated history, personal data, tokens, or private paths.

### Q. How do blocked and resume work?

A. Save the reason, evidence, and question in the Workpad; update status to blocked; and stop dispatch. After an answer, save the decision and normally resume the same Issue and Codex thread.

### Q. When is work a same-Task continuation?

A. Revisions with the same objective and host continue the same Task. A changed objective or host gets a checkpointed successor Issue.

### Q. How are Results imported?

A. Ask ChatGPT to “pull in the results.” It reads the Workpad, PR, verification, and Git state into the original Plan. The full Codex log is normally unnecessary.

### Q. What are Symphony and Codex responsible for?

A. Symphony orchestrates Issue polling, workspaces, retries, and threads / turns. Codex performs and verifies repository work.

### Q. Does `No queued retries` mean success?

A. No. It only says no retry is queued. Inspect Issue state, runtime logs, Workpad, commits / diff, verification, and PR together.

## execution_target policy

Use the execution host's hostname as the default identity. It must be unique within the LAN or organizational scope and remain unchanged for the Issue lifetime. A host move creates a checkpointed successor Issue.

If a private hostname would leak infrastructure in a public repository, use a non-sensitive hostname or public alias such as `build-public-01`, and keep the mapping outside public artifacts. Do not rewrite an existing Issue's `execution_target`.

## Status labels

| Label | Color | Description |
| --- | --- | --- |
| `symphony-ready` | `0E8A16` | Routing / execution control; not workflow status |
| `nd-status:scheduled` | `C2E0C6` | Human GO complete; waiting to run |
| `nd-status:running` | `1D76DB` | Codex execution in progress |
| `nd-status:blocked` | `D93F0B` | Waiting for human, external condition, or quota |
| `nd-status:review` | `FBCA04` | Waiting for Human review |
| `nd-status:failed` | `B60205` | Cannot continue automatically; inspect the cause |

Keep only one `nd-status:*` active. Do not remove `symphony-ready` merely to display running. Create labels with `gh label create NAME --color HEX --description TEXT`; customize with the GitHub UI or `gh label edit OLD --name NEW --color HEX --description TEXT`. Synchronize the Skill, docs, and automation. Renaming `symphony-ready` also requires updating every profile's `required_labels` and rerunning smoke verification.

Failures before a Codex turn may have no automatic actor. Do not claim full automation; update `failed` / `blocked` from runtime logs, the Workpad, or Result ingestion through a human or ChatGPT.

## Uninstall

1. Disable or delete `excellent-nd` in ChatGPT Skill management.
2. Stop Symphony and remove systemd, container, login-item, or other auto-start configuration.
3. Retain host-local WORKFLOW / profiles for rollback, or delete them safely.
4. After stopping profiles, stop using `symphony-ready` and optionally clean unused labels.
5. Revoke GitHub / Codex credentials and tokens at the provider and remove host copies without recording their values.
6. After audit and recovery checks, optionally delete workspaces, caches, and logs.
7. Normally retain Issues, PRs, commits, and history as audit records.

Uninstalling Excellent-Nd does not delete Codex or GitHub.

## Troubleshooting

If an Issue is not dispatched, check GitHub native state, adapter connectivity, profile `required_labels`, `symphony-ready`, and target conditions. If status is unclear, inspect runtime logs, the Workpad, Git diff, verification, and PR in that order. Never paste secrets into diagnostic records.
