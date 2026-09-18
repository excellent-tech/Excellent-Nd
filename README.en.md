# Excellent-Nd

Excellent-Nd is a project built around [OpenAI Symphony](https://github.com/openai/symphony). It aims to provide a conversation-first, ChatGPT-first Plan-and-Execute workflow that turns only approved work from a ChatGPT Plan into executable Tasks for Codex.

> The project is at an early stage. We are organizing the public design and validating the V1 end-to-end execution path; no usable implementation is available yet.

[日本語](README.md) | [简体中文](README.zh-CN.md)

## Problem to solve

In small teams and near-individual development, the same people often handle requirements, planning, task assignment, implementation, and verification. Manually creating and maintaining an Issue for every small task can itself become management overhead.

Excellent-Nd uses ChatGPT as the primary UI for requirements, planning, task assignment, Human GO, and result review. After Human GO, executable Tasks are persisted as GitHub Issues and handed to Symphony / Codex. Humans do not need to treat Issue management as the primary UI; they pull only the results they need back into ChatGPT.

Instead of passing the full chat history to Codex, each Task carries a compact Execution Packet containing its objective, constraints, acceptance criteria, relevant decisions, and references. Results are also kept structured rather than returning the full Codex log.

## Basic flow

```text
Human + ChatGPT
  requirements → Plan → task split / assignment → Human GO
                                           ↓
GitHub Issues
  Execution Packet / routing per Task
                                           ↓
Symphony
                                           ↓
Codex thread per Task
                                           ↓
Git / Test / PR / Issue Result
                                           ↓
Human: "Pull in the results"
                                           ↓
ChatGPT + Human
  review multiple Task results → merge back into Plan → next decision
```

One ChatGPT conversation may produce one or more Tasks. In single-person work, 1 Chat → 1 Task will be common. In multi-person work, 1 Chat may branch into multiple Tasks and multiple Codex threads.

V1 also supports rough workload allocation such as “split Tasks 1–10 between owner A and owner B at roughly 30:70.” The ratio is treated as approximate total workload, not a strict count of Tasks, and considers dependencies, parallelizability, and estimated effort.

## Relationship with Symphony

Symphony provides a specification and reference implementation for Issue-first orchestration: it monitors an issue tracker and runs Codex App Server inside a per-Issue workspace.

Excellent-Nd does not reimplement Symphony's:

- issue polling / dispatch
- workspace management
- retry / concurrency
- Codex App Server launch
- thread / turn management
- continuation
- execution telemetry

In V1, executable Tasks are persisted as GitHub Issues and run through Symphony's Issue-first execution.

This means the human-facing UX is conversation-first while the internal execution model is issue-first.

## V1 scope

V1 focuses on this path:

> Create a Plan in ChatGPT → split it into 1..N Tasks and assign owners → Human GO → create one GitHub Issue per Task → execute through Symphony / Codex → persist results in GitHub → human asks ChatGPT to pull in the results → ChatGPT merges them back into the original Plan

The bootstrap Task that installs the Symphony runtime on the first execution host—or on a later host that cannot be provisioned through the existing path—is a limited exception. After Human GO, its objective, acceptance criteria, and verification method are recorded in a GitHub Issue, and a human explicitly starts it through Codex CLI or an equivalent tool on the target host. The measured version set and verification results are then saved to the Issue. After runtime validation, work moves to normal Issue-first execution; this exception is not a general manual execution path.

V1 does not implement custom push notifications into ChatGPT, a custom Codex Runner, custom database, custom scheduler, custom Kanban, large Web UI, multi-agent orchestration, multiple AI providers, SaaS, or multi-tenancy.

See [Design](docs/design.md), [V1 Scope](docs/v1-scope.md), and [Open Questions](docs/open-questions.md). The Japanese documents are authoritative for design and specification decisions.


## ChatGPT Skill

The shared ChatGPT workflow is managed under [skills/excellent-nd](skills/excellent-nd/). The Skill standardizes Plan splitting, Human GO, Issue creation, Task control and correlation metadata, result import, Human Gate handling, and host migration rules. It does not add a new communication infrastructure.

Installing the Skill **only enables the ChatGPT-side operating rules**. It does not mean that the Symphony / Codex runtime has been installed or configured, or that V1 end-to-end validation has completed. V1 execution separately requires working Symphony, Codex, and GitHub integration on an execution host.
