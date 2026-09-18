# Excellent-Nd

Excellent-Nd 是一个基于 [OpenAI Symphony](https://github.com/openai/symphony) 的项目，目标是实现 Conversation-first / ChatGPT-first 的 Plan-and-Execute 工作流：只把 ChatGPT 中形成的计划里真正需要执行的工作交给 Codex。

> 项目目前处于开发早期阶段。当前正在整理公开设计并验证 V1 的执行路径，尚无可用实现。

[日本語](README.md) | [English](README.en.md)

## 要解决的问题

在小规模或接近个人开发的场景中，如果把讨论、调查和细小工作全部转成 Issue，管理本身就会成为负担。另一方面，把完整会话历史交给执行代理会增加无关上下文和 token 消耗。

Excellent-Nd 以 ChatGPT 作为需求整理、计划和决策的主要 UI，只把经人工批准的执行内容整理成小型 Task。传给 Codex 的内容包括目标、约束、验收条件、相关决策和参考信息；返回 ChatGPT 的则是变更、验证、风险和剩余工作等结构化信息。

## 基本流程

```text
Human + ChatGPT: 需求确认 → Plan → Human GO
                                  ↓
Excellent-Nd workflow:       准备 1 个 Task
                                  ↓
Execution:
  ├─ Durable Task → Symphony → Codex
  └─ lightweight Task → 执行路径待验证 → Codex
                                  ↓
ChatGPT + Human:       确认 Result → 下一步决策
```

我们称之为 Conversation-first / Plan-and-Execute。并非所有思考都要转成 Issue：短时、单人工作使用 lightweight Task；需要共享、交接、长期记录或 Human Gate 的工作使用基于 GitHub Issue 的 Durable Task。V1 不会自动分类。

## 与 Symphony 的关系

Symphony 提供 orchestration 的规范和 reference implementation：监视 Issue tracker，并在每个 Issue 的 workspace 中运行 Codex App Server。Excellent-Nd 不会重新实现其执行管理、workspace、retry、concurrency、thread / turn 管理或执行 telemetry。

Durable Task 利用 Symphony 擅长的 Issue-first execution；Excellent-Nd 则专注于从 ChatGPT 的 Plan 中提取执行所需信息，并把结果返回会话。无需创建 Issue 的 lightweight Task 的最小执行路径尚未确定，是 V1 开始前的验证事项。

## V1 范围

V1 只聚焦以下一条路径：

> 在 ChatGPT 中创建 Plan → Human GO → 将 1 个 Task 交给 Codex → 执行 → 在 ChatGPT 中确认结构化 Result

ChatGPT 是主要 UI；运行 Codex 的 Git 管理开发环境是执行目标；Symphony 是 Issue-first orchestration 基础；GitHub 只在需要时用于 Issue、PR 和共享记录。

自建 Codex Runner、自建 agent harness、自建 Kanban、大型 Web UI、中央数据库、通知基础设施、multi-agent、多 AI provider、SaaS、multi-tenant 和通用 workflow engine 均不属于 V1。

详情请参阅[设计](docs/design.md)、[V1 范围](docs/v1-scope.md)和[未确定事项](docs/open-questions.md)。日文资料是设计和规范的正式版本。
