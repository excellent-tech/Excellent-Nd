# Excellent-Nd Runtime Architecture Guide

[日本語 (authoritative)](runtime-architecture.md) | [简体中文](runtime-architecture.zh-CN.md)

This guide explains Excellent-Nd for readers who are new to GitHub Issues, OpenAI Symphony, and Codex App Server. Its goal is to make it possible to trace what happens, in what order, and which source code is responsible.

The Japanese version is authoritative. For installation and day-to-day operations, see the [User Guide](operations.en.md). For design goals, see [Design](design.md).

> "Symphony" here means the `openai/symphony` runtime pinned by `config/runtime-lock.json`. Treat that file as the source of truth for the validated version. For upstream behavior, see the [OpenAI Symphony SPEC](https://github.com/openai/symphony/blob/main/SPEC.md) and [Elixir implementation README](https://github.com/openai/symphony/blob/main/elixir/README.md).

---

## 1. Core terms

| Term | Beginner meaning | Role in Excellent-Nd |
| --- | --- | --- |
| ChatGPT | Main human planning and decision UI | Task split, Human GO, result ingestion |
| GitHub Issue | One durable work ticket | Durable Task, Execution Packet, Workpad |
| Execution Packet | Instructions given to Codex | Entire Issue body |
| routing label | Switch that makes a Task dispatchable | Usually `symphony-ready` |
| target label | Selects which execution host may pick it up | `nd-target:<execution_target>` |
| workflow status | Logical Task state | `scheduled / running / blocked / review` |
| repository-native status | Repository's own progress surface | labels or a GitHub Project field |
| Symphony | Coding-agent orchestrator | polling, workspace, hooks, retry, Codex launch |
| workspace | Per-Issue working directory | normally one workspace per Issue |
| observer | Excellent-Nd process around Symphony | state synchronization and interruption handling |
| Codex App Server | Coding worker process | repository investigation, changes, verification |
| Workpad | Durable execution evidence on the Issue | start, blocker, verification, handoff |
| transition | Formal lifecycle update | body, routing, repository status, Workpad |
| fail closed | Stop when correctness cannot be proven | disable routing and preserve evidence |

Excellent-Nd is conversation-first for humans and Issue-first internally. The Issue is a durable execution record, not the primary human UI.

---

## 2. End-to-end flow

```mermaid
flowchart TD
    A[Human + ChatGPT<br/>Plan / Human GO] --> B[GitHub Issue<br/>Execution Packet]
    B --> C[Repository config / dispatch gates]
    C -->|PASS| D[Routing + target labels]
    D --> E[Symphony polling]
    E --> F[Per-Issue workspace]
    F --> G[before_run safety hook]
    G --> H[Symphony worker pickup]
    H --> I[observer: execution_started]
    I --> J[GitHub.transition running]
    J --> K[Codex App Server]
    K --> L[Change / verification / Draft PR]
    L --> M[Structured lifecycle marker]
    M --> N[after_run hook]
    N --> O[GitHub.transition]
    O -->|review| P[Human review / merge]
    P --> Q[ChatGPT result ingestion]
    Q --> R[Issue close / next Task]
```

Blocked execution follows the same state path: a pre-run safety failure, task-level marker, or runtime interruption is converted into a formal `blocked` transition, routing is disabled, evidence is stored, and resume requires gates to pass again.

---

## 3. Symphony vs Excellent-Nd

Upstream Symphony polls an issue tracker, manages per-Issue workspaces, runs lifecycle hooks, launches a coding agent, and manages retries, continuation, and concurrency.

Excellent-Nd adds policy and GitHub lifecycle synchronization around that runtime.

| Area | Primary owner | Excellent-Nd source |
| --- | --- | --- |
| Issue polling | Symphony | generated `WORKFLOW.md` |
| required-label filtering | Symphony | `config/WORKFLOW.md.tpl` |
| workspace lifecycle | Symphony | workspace config + hooks |
| retry / continuation | Symphony | upstream runtime |
| Codex launch | Symphony | `codex.command` |
| Human GO / Plan | Excellent-Nd Skill | `skills/excellent-nd/` |
| repository gates | Excellent-Nd | `scripts/repository_adapter.py` |
| target routing | Excellent-Nd | `scripts/execution_target.py` |
| workspace safety | Excellent-Nd | `runtime_observer.py::prepare_workspace` |
| running-state detection | Excellent-Nd | `runtime_observer.py::run_observer` |
| Project status mapping | Excellent-Nd | `repository_adapter.py::transition_event` |
| blocked/review/failed handoff | Excellent-Nd | structured marker + observer |
| service management | Excellent-Nd | systemd helpers |
| version pin / setup / smoke | Excellent-Nd | `runtime-lock.json`, `setup.py`, `smoke.py` |

Symphony hooks used by Excellent-Nd:

- `after_create`: initialize a newly created workspace
- `before_run`: safety check before Codex starts; failure aborts the attempt
- `after_run`: lifecycle handoff after an attempt

---

## 4. Node-by-node implementation map

### ChatGPT / Human GO

Sources:

- `skills/excellent-nd/SKILL.md`
- `skills/excellent-nd/references/task-schema.md`
- `skills/excellent-nd/references/workflow.md`

Output: a GitHub Issue whose body is the Execution Packet.

### Repository integration and gates

Sources:

- `scripts/repository_config.py`
- `scripts/repository_adapter.py::resolve_context`
- `scripts/repository_adapter.py::evaluate_gates`
- `scripts/repository_adapter.py::preflight`

Excellent-Nd does not hard-code repository-specific fields such as Status, Agent, or Human Approval. A consumer repository configures only the gates it uses in `.excellent-nd/repository.json`.

Unavailable or ambiguous required data fails closed.

### Routing and execution target

Sources:

- `scripts/execution_target.py`
- `.excellent-nd/targets/*.json`
- `config/WORKFLOW.md.tpl`

A routing label controls dispatchability; a target label identifies the host. `enabled: true` in target inventory means configured/assignable, not an online heartbeat.

### Setup and service

Sources:

- `scripts/setup.py`
- `scripts/smoke.py`
- `scripts/service_runner.py`
- `scripts/systemd_service.py`
- `config/runtime-lock.json`

Setup validates prerequisites, downloads the pinned Symphony asset, verifies its checksum, generates `WORKFLOW.md`, runs smoke checks, writes host/target identity, and may install/restart the systemd user service.

### Symphony polling and workspace

Sources:

- `config/WORKFLOW.md.tpl`
- generated `.excellent-nd/WORKFLOW.md`
- upstream Symphony

The polling implementation itself is upstream Symphony code, not Excellent-Nd Python code.

### before_run workspace safety

Sources:

- `runtime_observer.py::prepare_workspace`
- `runtime_observer.py::workspace_decision`

Behavior:

| Workspace | Base relation | Result |
| --- | --- | --- |
| clean | drifted | refresh to remote default branch |
| dirty | same base | preserve and continue |
| dirty | drifted | block before Codex starts |

Dirty + drift is not auto-reset because uncommitted work might be valuable evidence.

### Worker pickup -> running

Sources:

- `runtime_observer.py::worker_started_issue`
- `runtime_observer.py::run_observer`
- `runtime_observer.py::GitHub.transition`

Only the validated exact Symphony worker-start event is accepted. A matching event becomes `running`, which maps to the repository event `execution_started`.

### Formal lifecycle transition

Sources:

- `runtime_observer.py::GitHub.transition`
- `runtime_observer.py::runtime_event_for`
- `repository_adapter.py::transition_event`

Order:

1. remove routing
2. update Issue body workflow status
3. update repository-native status when configured
4. write Workpad evidence
5. restore routing only when the final state needs it and all prior updates succeeded

If an intermediate update fails, routing remains disabled.

### Codex execution and publication

The workflow launches `codex app-server` under `workspace-write`. Codex should not bypass protected Git metadata. Repository publication uses the host-side `github_api` path described in `WORKFLOW.md.tpl`.

### Structured lifecycle marker and after_run

Marker file:

`.excellent-nd/runtime-transition.json`

Schema:

`excellent-nd/runtime-transition@v1`

Sources:

- `validate_transition_marker`
- `apply_transition_marker`
- `transition_identity`
- `validated_receipt`

Allowed transitions are `blocked`, `review`, and `failed`. Receipts bind repository, Issue, run, attempt, and transition for idempotency. Missing, corrupt, unknown, or invalid markers fail closed to blocked.

### Runtime interruptions

Sources:

- `classify_interruption`
- `extract_context`
- `interruption_workpad`
- `run_observer`

Examples include quota exhaustion, long rate limits, turn timeout, App Server startup failure, and abnormal agent exit.

### Human review and result ingestion

Review disables routing. Human review/merge remains a gate. ChatGPT later reads the Issue, PR, and verification and reintegrates the result into the original Plan.

---

## 5. The five state surfaces

| Surface | Example | Meaning |
| --- | --- | --- |
| GitHub Issue native state | open / closed | Active vs terminal ticket |
| `workflow_status` | scheduled / running / blocked / review | Excellent-Nd logical state |
| routing label | `symphony-ready` | Whether Symphony may pick it up |
| target label | `nd-target:worker-a` | Which host may pick it up |
| repository-native status | Todo / Working / Hold | Consumer repository's status authority |

Normal transitions keep these surfaces consistent. Status authority is configured in `.excellent-nd/repository.json` as either labels or a GitHub Project field.

---

## 6. State model

```mermaid
stateDiagram-v2
    [*] --> scheduled: Human GO / resume
    scheduled --> running: worker pickup
    running --> review: verification / handoff
    running --> blocked: task blocker
    running --> blocked: runtime interruption
    scheduled --> blocked: before_run safety failure
    blocked --> scheduled: Human GO + gates PASS
    running --> blocked: transition failure / fail closed
    review --> [*]: Human merge + result ingestion + close
```

---

## 7. Unexpected defects and improvements discovered so far

This section records Excellent-Nd Core findings. Consumer-repository policy conflicts are a different class of problem.

| Finding | Impact | Fix / lesson | Related |
| --- | --- | --- | --- |
| Routing and visible status were easy to conflate | UI changes could alter dispatch semantics | Separate routing from status | PR #7 |
| execution_target metadata alone did not route to a specific host | Multiple hosts could not be safely distinguished | Add target-specific routing labels and inventory | PR #11 |
| setup missed the `write_target_record` import | Setup could pass smoke and fail afterwards | Add import + regression test | PR #13 |
| Repository / Issue integration was not a first-class installation layer | Existing labels/automation could conflict | Add explicit integration review and config SSOT | PR #15 |
| Repository-specific Project fields could not be assumed globally | Core became repository-specific | Generic event mapping and dispatch gates | PR #17 |
| CI could report success with zero discovered tests; invalid repository path input was accepted | False confidence and weak input validation | Real test discovery + fail-closed validation | PR #18 |
| Foreground runtime was weak for long-running hosts | Harder restart/status/log operations | systemd user service lifecycle | PR #21 |
| Worker pickup was not connected to `execution_started` | Codex could run while UI still looked not-started | Parse only the validated worker-start event | Issue #22 / PR #23 |
| Task-level blocker could stop with comment-only evidence | body/routing/Project status could diverge | Structured marker -> formal transition | Issue #22 / PR #23 |
| Dirty workspace could remain on an old base and still start Codex | stale-base execution | dirty + base drift blocks before Codex | Issue #22 / PR #23 |

### Core vs consumer repository

A Core bug reproduces independently of one repository's business rules—for example worker-start state propagation or hook handling.

A consumer repository problem depends on that repository's policy or mapping—for example an incorrect `.excellent-nd/repository.json` gate or contradictory local governance.

Do not solve a consumer-specific rule by hard-coding it into Excellent-Nd Core.

A useful question is:

> Would the same input reproduce in another repository with equivalent configuration?

---

## 8. Debugging order

When the UI does not clearly show whether work is running:

1. GitHub Issue native state
2. `workflow_status`
3. routing / target labels
4. repository-native status
5. latest Workpad
6. branch / PR
7. systemd service
8. observer / Symphony process
9. runtime journal
10. workspace HEAD and dirty state

Host checks:

```sh
systemctl --user status 'excellent-nd@<instance>.service' --no-pager
systemctl --user is-active 'excellent-nd@<instance>.service'
journalctl --user -u 'excellent-nd@<instance>.service' -n 100 --no-pager
pgrep -af 'runtime_observer.py|symphony'
```

Workspace checks:

```sh
git status --short
git rev-parse HEAD
git diff --check
```

Always compare against a freshly fetched remote default-branch head.

---

## 9. Source code map

| Question | Start here |
| --- | --- |
| Project overview | `README.md`, `docs/design.md` |
| Operator procedures | `docs/operations.en.md` |
| Human GO / Skill | `skills/excellent-nd/SKILL.md` |
| Task metadata | `skills/excellent-nd/references/task-schema.md` |
| Repository config | `scripts/repository_config.py` |
| Dispatch gates | `repository_adapter.py::preflight` |
| Project status update | `repository_adapter.py::transition_event` |
| Runtime version pin | `config/runtime-lock.json` |
| Workflow template | `config/WORKFLOW.md.tpl` |
| Execution targets | `scripts/execution_target.py` |
| Setup | `scripts/setup.py` |
| Smoke | `scripts/smoke.py` |
| Service start | `scripts/service_runner.py` |
| Worker start observer | `runtime_observer.py::run_observer` |
| Formal transition | `runtime_observer.py::GitHub.transition` |
| Workspace preflight | `runtime_observer.py::prepare_workspace` |
| Structured marker | `runtime_observer.py::apply_transition_marker` |
| Runtime interruption | `runtime_observer.py::classify_interruption` |
| Regression tests | `tests/test_runtime_observer.py` |

---

## 10. Recommended reading order

1. this guide
2. `README.md`
3. `docs/operations.en.md`
4. `config/WORKFLOW.md.tpl`
5. `scripts/runtime_observer.py`
6. `scripts/repository_adapter.py`
7. `tests/test_runtime_observer.py`
8. upstream Symphony SPEC when deeper details are needed

Update this guide whenever lifecycle nodes, hook contracts, state authority, routing semantics, workspace recovery, or pinned Symphony/Codex behavior changes.