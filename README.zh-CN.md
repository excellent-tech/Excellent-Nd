# Excellent-Nd

Excellent-Nd 是一个开源的 **AI驱动开发工作流**：它以 ChatGPT 为计划与判断中心，连接 GitHub Issues、[OpenAI Symphony](https://github.com/openai/symphony) 和 Codex 执行开发 Task，采用 Conversation-first / Plan-and-Execute 模式，并提供 excellent-nd Skill 作为 ChatGPT 侧操作接口。

> 第一个常规单任务端到端流程已经验证。项目处于面向 1.0 正式版的 beta / development 系列，结果拉取、continuation 和多任务场景仍在验证。

[日本語](README.md) | [English](README.en.md)

## 要解决的问题

在小规模或接近个人开发的场景中，同一批成员往往需要同时负责需求整理、计划、任务分配、实现和验证。如果每个小任务都由人工创建和维护 Issue，管理本身可能成为额外负担。

Excellent-Nd 以 ChatGPT 作为需求整理、计划、任务分配、人工执行确认（Human GO） 和结果确认的主要 UI。人工执行确认（Human GO） 后，实际执行的 Task 会作为 GitHub Issue 持久化，并交给 Symphony / Codex。人不需要把 Issue 管理当作主要 UI，只需把需要的结果拉回 ChatGPT。

不会把完整聊天历史交给 Codex，而是为每个 Task 生成精简的 Execution Packet，包括目标、约束、验收条件、相关决策和参考信息。返回结果也以结构化信息为主，而不是完整 Codex 日志。

## 基本流程

```text
Human + ChatGPT
  需求确认 → Plan → Task拆分 / 分配 → 人工执行确认（Human GO）
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

1.0.x 还支持类似“把 Task 1～10 按约 3:7 的工作量分给负责人A和负责人B”这样的概算分配。该比例表示大致总工作量，而不是严格的 Task 数量比例，并考虑依赖关系、可并行性和预估工作量。

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

1.0.x 中，实际执行的 Task 都会先作为 GitHub Issue 持久化，再使用 Symphony 的 Issue-first execution。

因此，对人的 UX 是 Conversation-first，内部执行模型则是 Issue-first。

## 1.0.x 范围

1.0.x 聚焦以下路径：

> 在 ChatGPT 中创建 Plan → 拆分为 1..N 个 Task 并分配负责人 → 人工执行确认（Human GO） → 为每个 Task 创建 GitHub Issue → 通过 Symphony / Codex 执行 → 将结果保存到 GitHub → 人在原 Chat 中要求“拉取结果” → ChatGPT 将结果重新合并到原 Plan

在第一台 execution host，或无法通过现有路径完成 provisioning 的后续 host 上安装 Symphony runtime 的 bootstrap Task，是一项受限例外。人工执行确认（Human GO） 后，先在 GitHub Issue 中记录目标、验收条件和验证方法，再由人明确地从目标 host 上的 Codex CLI 或同等工具启动；随后将实测 version set 和验证结果保存到 Issue。runtime 验证完成后即转入通常的 Issue-first execution；该例外不是通用的手动执行路径。

1.0.x 不实现 ChatGPT 自动 push、自建 Codex Runner、自建数据库、自建 scheduler、自建 Kanban、大型 Web UI、multi-agent、多 AI provider、SaaS 或 multi-tenant。

详情请参阅[设计](docs/design.md)、[1.0.x 范围](docs/v1-scope.md)和[未确定事项](docs/open-questions.md)。日文资料是设计和规范的正式版本。


## ChatGPT Skill

Excellent-Nd 的通用 ChatGPT workflow 在 [skills/excellent-nd](skills/excellent-nd/) 中管理。该 Skill 用于标准化 Plan 拆分、人工执行确认（Human GO）、Issue 创建、Task control / correlation metadata、结果拉取、人工决策关口（Human Gate） 和 host 迁移规则，并不会新增通信基础设施。

安装该 Skill **只会启用 ChatGPT 侧的操作规则**。这并不表示 Symphony / Codex runtime 已完成安装和配置，也不表示 1.0.x 端到端验证已经完成。1.0.x 执行仍需要在 execution host 上另行准备可用的 Symphony、Codex 和 GitHub 集成。

## 职责与使用指南

| Component | 职责 |
| --- | --- |
| Excellent-Nd | 开源项目 / AI驱动开发工作流 |
| excellent-nd Skill | ChatGPT 侧计划、人工执行确认（Human GO） 与操作接口 |
| GitHub | 持久任务、Execution Packet、checkpoint、PR / 结果 |
| Symphony | Issue-first 执行编排 |
| Codex | 任务执行 worker |

安装、运行、常见问题、卸载、标签和 `execution_target` 请参阅[使用指南](docs/operations.zh-CN.md)；版本编号请参阅[版本方针](skills/excellent-nd/references/version-policy.md)。
