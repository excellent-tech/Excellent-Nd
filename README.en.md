# Excellent-Nd

Excellent-Nd is a project built around [OpenAI Symphony](https://github.com/openai/symphony). It aims to provide a conversation-first, ChatGPT-first Plan-and-Execute workflow that sends only the necessary work from a ChatGPT plan to Codex.

> The project is at an early stage. We are organizing the public design and validating the V1 execution path; no usable implementation is available yet.

[日本語](README.md) | [简体中文](README.zh-CN.md)

## Problem to solve

For small teams and near-individual development, turning every discussion, investigation, and small task into an issue can make task management a burden of its own. Passing an entire conversation history to an execution agent also adds irrelevant context and token usage.

Excellent-Nd uses ChatGPT as the primary UI for refining requirements, planning, and decisions. Only work approved by a human is packaged as a small Task. Codex receives the objective, constraints, acceptance criteria, relevant decisions, and references. ChatGPT receives structured information such as changes, verification, risks, and remaining work.

## Basic flow

```text
Human + ChatGPT: clarify requirements → Plan → Human GO
                                               ↓
Excellent-Nd workflow:                  prepare 1 Task
                                               ↓
Symphony / Codex:             implement, investigate, verify
                                               ↓
ChatGPT + Human:              review Result → next decision
```

We call this Conversation-first / Plan-and-Execute. Not every thought becomes an issue: short, single-person work can remain a lightweight Task, while work requiring sharing, handoff, long-lived history, or a Human Gate becomes a Durable Task backed by a GitHub Issue. V1 will not automate this classification.

## Relationship with Symphony

Symphony provides a specification and reference implementation for orchestration that monitors an issue tracker and runs Codex App Server in a per-issue workspace. Excellent-Nd will not reimplement its execution management, workspace handling, retries, concurrency, thread / turn management, or execution telemetry.

Durable Tasks use Symphony's Issue-first execution. Excellent-Nd focuses on extracting only the information required for execution from a ChatGPT Plan and returning the result to the conversation. The minimum execution path for a lightweight Task without an issue is undecided and must be validated before V1 implementation.

## V1 scope

V1 focuses on one path:

> Create a Plan in ChatGPT → Human GO → send 1 Task to Codex → execute → review a structured Result in ChatGPT

ChatGPT is the primary UI; a Git-managed development environment that can run Codex is the execution target; Symphony is the Issue-first orchestration foundation; and GitHub is used for Issues, PRs, and shared history when needed.

A custom Codex Runner, custom agent harness, custom Kanban, large Web UI, central database, notification infrastructure, multi-agent orchestration, multiple AI providers, SaaS, multi-tenancy, and a general-purpose workflow engine are outside V1.

See [Design](docs/design.md), [V1 Scope](docs/v1-scope.md), and [Open Questions](docs/open-questions.md). The Japanese documents are authoritative for design and specification decisions.
