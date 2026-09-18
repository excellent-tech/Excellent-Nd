# Excellent-Nd

Excellent-Nd 是一个基于 [OpenAI Symphony](https://github.com/openai/symphony) 的项目，目标是实现 Conversation-first / ChatGPT-first 的 Plan-and-Execute 工作流：只把 ChatGPT 计划中经人工确认需要执行的工作整理成 Task，并交给 Codex 执行。

> 项目目前处于开发早期阶段。当前正在整理公开设计并验证 V1 的端到端执行路径，尚无可用实现。

[日本語](README.md) | [English](README.en.md)

## 要解决的问题

在小规模或接近个人开发的场景中，同一批成员往往需要同时负责需求整理、计划、任务分配、实现和验证。如果每个小任务都由人工创建和维护 Issue，管理本身可能成为额外负担。

Excellent-Nd 以 ChatGPT 作为需求整理、计划、任务分配、Human GO 和结果确认的主要 UI。Human GO 后，实际执行的 Task 会作为 GitHub Issue 持久化，并交给 Symphony / Codex。人不需要把 Issue 管理当作主要 UI，只需把需要的结果拉回 ChatGPT。

不会把完整聊天历史交给 Codex，而是为每个 Task 生成精简的 Execution Packet，包括目标、约束、验收条件、相关决策和参考信息。返回结果也以结构化信息为主，而不是完整 Codex 日志。

## 基本流程

```text
Human + ChatGPT
  需求确认 → Plan → Task拆分 / 分配 → Human GO
                                      ↓
GitHub Issues
  每个Task的 Execution Packet / routing
                                      ↓
Symphony
                                      ↓
每个Task对应一个 Codex thread
                                      ↓
Git / Test / PR / Issue Result
                                      ↓
Human: “把结果拉回来”
                                      ↓
ChatGPT + Human
  汇总多个Task结果 → 合并回原Plan → 下一步判断
```

一个 ChatGPT 会话可以生成一个或多个 Task。单人工作时，1 Chat → 1 Task 会比较常见；多人工作时，1 Chat 可以拆成多个 Task，并分别由不同 Codex thread 执行。

V1 还支持类似“把 Task 1～10 按约 3:7 的工作量分给负责人A和负责人B”这样的概算分配。该比例表示大致总工作量，而不是严格的 Task 数量比例，并考虑依赖关系、可并行性和预估工作量。

## 与 Symphony 的关系

Symphony 提供 Issue-first orchestration 的规范和 reference implementation：监视 Issue tracker，并在每个 Issue 的 workspace 中运行 Codex App Server。

Excellent-Nd 不会重新实现 Symphony 已提供的：

- Issue polling / dispatch
- workspace 管理
- retry / concurrency
- Codex App Server 启动
- thread / turn 管理
- continuation
- execution telemetry

V1 中，实际执行的 Task 都会先作为 GitHub Issue 持久化，再使用 Symphony 的 Issue-first execution。

因此，对人的 UX 是 Conversation-first，内部执行模型则是 Issue-first。

## V1 范围

V1 聚焦以下路径：

> 在 ChatGPT 中创建 Plan → 拆分为 1..N 个 Task 并分配负责人 → Human GO → 为每个 Task 创建 GitHub Issue → 通过 Symphony / Codex 执行 → 将结果保存到 GitHub → 人在原 Chat 中要求“拉取结果” → ChatGPT 将结果重新合并到原 Plan

V1 不实现 ChatGPT 自动 push、自建 Codex Runner、自建数据库、自建 scheduler、自建 Kanban、大型 Web UI、multi-agent、多 AI provider、SaaS 或 multi-tenant。

详情请参阅[设计](docs/design.md)、[V1 范围](docs/v1-scope.md)和[未确定事项](docs/open-questions.md)。日文资料是设计和规范的正式版本。
