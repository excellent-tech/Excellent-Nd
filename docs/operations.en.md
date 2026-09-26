# User Guide

[日本語 (authoritative)](operations.md) | [简体中文](operations.zh-CN.md)

This guide is for operators installing, running, and disabling Excellent-Nd. See the [version policy](../skills/excellent-nd/references/version-policy.md) for numbering rules and the current candidate.


## Three installation levels

Configure Excellent-Nd in this order: **Skill → Repository / Issue integration → Execution host**. See [Repository / Issue integration](repository-onboarding.en.md).

Do not start execution-host setup until `.excellent-nd/repository.json` records a completed review of labels, Issue templates, and automation. Prefer asking ChatGPT to audit the repository and propose the mapping.

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

### 3. Configure Repository / Issue integration

- **Action**: Configure the target repository and authentication.
- **Command / UI**: Grant a GitHub App or official integration minimum permissions for Issues, labels, branches, and PRs. Store secrets in the host secret store.
- **Expected result**: A test Issue can be read and written, and required branch and PR operations work.
- **If OK**: Continue to step 4.
- **If not OK**: Correct installation scope, permissions, and repository selection. Do not paste secrets into Issues or logs.

### 4. Acquire the validated runtime

- **Action**: Acquire the pinned upstream Symphony release.
- **Command / UI**: Run `python3 scripts/setup.py --repo OWNER/REPOSITORY --prefix .excellent-nd --skill-confirmed`; keep `.excellent-nd/` outside Git.
- **Expected result**: The asset matches the SHA-256 in `config/runtime-lock.json`.
- **If OK**: Continue to step 5.
- **If not OK**: Check platform, release asset, and network; stop on checksum mismatch.

### 5. Check Codex App Server compatibility

- **Action**: Check Codex version and approval / sandbox policy.
- **Command / UI**: Run `codex --version`; setup checks the exact version and `approval_policy: never`.
- **Expected result**: The manifest version matches and App Server is available.
- **If OK**: Continue to step 6.
- **If not OK**: Do not reuse another version's settings; stop until validated.

### 6. Check WORKFLOW and the GitHub Issues adapter

- **Action**: Inspect `.excellent-nd/WORKFLOW.md`.
- **Command / UI**: Check repository, `required_labels: symphony-ready`, `{{ issue.description }}`, workspace, and Codex policy.
- **Expected result**: The full Issue body reaches the initial prompt and ineligible Issues are not dispatched. For the GitHub adapter, a host-side `before_run` hook refreshes a clean workspace to the remote default branch outside the Codex sandbox; Codex keeps `.git` protected under `workspace-write`, uses read-only Git verification, and publishes branch / commit / Draft PR state through host-side `github_api`.
- **If OK**: Continue to step 7.
- **If not OK**: Fix and regenerate the template; do not use a title-only profile.

### 7. Check routing and status labels

- **Action**: Inspect labels created or updated by setup.
- **Command / UI**: Check `symphony-ready` and the five `nd-status:*` labels in GitHub.
- **Expected result**: Routing and visibility responsibilities are separate.
- **If OK**: Continue to step 8.
- **If not OK**: Align permissions, names, and profile `required_labels`.

> **Illustration candidate 3**: An Issue where `symphony-ready` and `nd-status:scheduled` are distinguishable. Exclude secrets and private hostnames / URLs.

### 8. Start Symphony through the observer

- **Action**: On Linux, start the observer and Symphony as a repository-scoped systemd user service.
- **Command / UI**: Add `--start` to the step 4 setup command. The repository basename is the default instance, such as `excellent-nd@sample-app.service`. Use a public-safe `--service-instance worker-a` only to resolve a basename collision. Use `--foreground` instead for terminal diagnostics.
- **Expected result**: Setup installs the shared template and instance mapping, reloads systemd, restarts and enables the unit, and verifies active observer/Symphony processes. The runtime no longer depends on the setup terminal.
- **If OK**: Continue to step 9.
- **If not OK**: Check binary, profile, `gh auth`, Codex auth, and the user journal; do not add another scheduler or polling daemon.

The service obtains a token from the same user's `gh auth token` at startup and passes it only in the process environment. It does not store credentials in the unit, mapping, or repository. Setup does not enable linger or make sudo/root changes.

> **Illustration candidate 2**: Show only a healthy process and loaded profile. Exclude tokens, private hostnames / paths, environment values, and internal URLs.

### 9. Run smoke verification

- **Action**: Check deterministic preflight and the live runtime.
- **Command / UI**: If needed, rerun `python3 scripts/smoke.py --runtime .excellent-nd/symphony --workflow .excellent-nd/WORKFLOW.md --repo OWNER/REPOSITORY`; verify no unintended dispatch in logs.
- **Expected result**: `readiness: PASS`, healthy startup, and no unintended dispatch.
- **If OK**: Continue to step 10.
- **If not OK**: Do not add the routing label; fix checksum, Codex version, GitHub auth, or WORKFLOW.

### 10. Persist readiness in the Workpad

- **Action**: Save measured versions, profile revision, verification, and residual risks to the bootstrap Issue.
- **Command / UI**: Comment only sanitized results.
- **Expected result**: The Issue alone shows whether E2E may start.
- **If OK**: Continue to step 11.
- **If not OK**: Keep normal Tasks non-dispatchable.

### 11. Run the first single-Task E2E

- **Action**: Run a normal Task only when the current user message has both `@excellent-nd` and explicit Human GO.
- **Command / UI**: Complete `ChatGPT → Issue → Symphony → Codex → branch / verification → PR → Human review`.
- **Expected result**: Change, verification, and PR are traceable; review removes the routing label in the same decision.
- **If OK**: Begin normal operations.
- **If not OK**: Inspect logs, Workpad, diff, verification, and PR; dispatch no more Tasks until resolved.
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

### Q. How do I check the execution-host runtime?

A. `enabled: true` in `.excellent-nd/targets/*.json` does not mean the service is currently online. Use service status, processes, Issue state, Workpad, and PR evidence together:

```sh
systemctl --user list-units 'excellent-nd@*.service' --all
systemctl --user status 'excellent-nd@<repository-instance>.service' --no-pager
systemctl --user is-active 'excellent-nd@<repository-instance>.service'
systemctl --user is-enabled 'excellent-nd@<repository-instance>.service'
journalctl --user -u 'excellent-nd@<repository-instance>.service' -n 100 --no-pager
pgrep -af 'runtime_observer.py|symphony'
```

Restart with `systemctl --user restart 'excellent-nd@<repository-instance>.service'`; `stop` and `start` work the same way. Routing labels cannot be picked up while the worker is stopped. Neither `Working 0`, `Inactive`, nor `No queued retries` alone proves the runtime's health or failure cause.

## Runtime interruption records and resume

The observer follows observable events in the same Symphony process tree. Only issue-scoped usage exhaustion, long rate limits, turn timeout, App Server startup failure, or abnormal agent exit creates a sanitized Workpad entry with category, error, occurred_at, available reset / retry and session / attempt values, checkpoint availability, remaining work, and resume condition. Short retries remain with Symphony and create no comment. Missing Issue or exact error data is reported as unavailable, never guessed.

An interruption updates `workflow_status=blocked`, `nd-status:blocked`, and removal of `symphony-ready` in the same Issue update. Review also removes routing in the same decision. Resume only after the current user message again contains `@excellent-nd` and Human GO.

```sh
python3 scripts/runtime_observer.py resume --repo OWNER/REPOSITORY --issue NUMBER \\
  --reason "resume condition verified" --explicit-mention --human-go
```

This records the decision and restores `scheduled`, `nd-status:scheduled`, and routing. Prefer the same Issue / thread; never redispatch unconditionally.

## Registering and removing multiple execution hosts

See [execution_target and execution-host inventory](execution-targets.en.md) for registration timing, adding multiple hosts, temporary disablement, removal, and re-registration.

In short, setup creates the local inventory record only after smoke PASS, and shared registration becomes effective after that file is committed and merged. Removal follows `disable -> drain/migrate active Tasks -> delete the target file`.
\n\n## execution_target policy

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

If an Issue is not dispatched, check GitHub native state, adapter connectivity, profile `required_labels`, `symphony-ready`, and target conditions. If status is unclear, inspect runtime logs, the Workpad, Git diff, verification, and PR in that order. Under Codex `workspace-write`, `.git` is intentionally protected from writes; do not fix `FETCH_HEAD` / branch / commit failures by changing ownership, permissions, or enabling `danger-full-access`. A clean workspace is refreshed by the host-side `before_run` hook, and GitHub publication uses Symphony's host-side `github_api`. Never paste secrets into diagnostic records.
