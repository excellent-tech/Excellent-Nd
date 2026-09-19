# 使用指南

[日本語（规范原文）](operations.md) | [English](operations.en.md)

本指南面向安装、运行和停用 Excellent-Nd 的操作者。版本编号规则和当前候选版本请参阅[版本方针](../skills/excellent-nd/references/version-policy.md)。

## 安装

### 1. 确认前提条件

- **要执行的操作**：准备 ChatGPT、GitHub 仓库和执行主机。
- **命令 / 界面操作**：确认 ChatGPT 可使用 Skill 与 GitHub 集成，GitHub 可操作 Issue、标签、分支和 PR，执行主机可使用 Git。
- **确认结果**：具备必要的最小权限，并可安全保存凭据。
- **如果正常**：进入步骤 2。
- **如果异常**：完善权限与密钥存储后再继续；不要公开凭据、令牌、内部主机名或内部 URL。

### 2. 安装 excellent-nd Skill

- **要执行的操作**：把 `skills/excellent-nd/` 安装到 ChatGPT。
- **命令 / 界面操作**：在 ChatGPT Skill 管理界面添加并启用。
- **确认结果**：Skill 列表中显示并可选择 `excellent-nd`。
- **如果正常**：进入步骤 3。
- **如果异常**：检查路径、权限和元数据；解决前不要配置运行环境。

> **插图候选 1**：截取 ChatGPT Skill 列表中可选择 `excellent-nd` 的画面。只显示名称和启用状态；不要显示聊天内容、令牌、账号信息或内部 URL。

### 3. 准备 GitHub

- **要执行的操作**：配置目标仓库与认证。
- **命令 / 界面操作**：通过 GitHub App 或官方集成授予 Issue、标签、分支和 PR 所需的最小权限，把秘密值保存在密钥存储中。
- **确认结果**：可以读写测试 Issue，并执行所需的分支和 PR 操作。
- **如果正常**：进入步骤 4。
- **如果异常**：修正安装范围、权限和仓库选择；不要把秘密值贴到 Issue 或日志。

### 4. 准备 Symphony 与 Codex

- **要执行的操作**：按上游文档在执行主机安装 Symphony 与 Codex CLI / App Server，并固定待验证的精确版本。
- **命令 / 界面操作**：安装后用版本显示命令记录实测值。
- **确认结果**：Symphony 与 Codex App Server 可启动，Git 和 GitHub 可连接。
- **如果正常**：进入步骤 5。
- **如果异常**：检查上游要求、权限、网络和认证；正常启动前不要派发 Issue。

> **插图候选 2**：截取 Symphony 启动后的正常状态。只显示进程运行并加载目标配置；不要显示令牌、内部主机名、内部路径、环境变量或内部 URL。

### 5. 配置 WORKFLOW、profile 和 GitHub Issues adapter

- **要执行的操作**：配置 adapter 与目标主机 profile。
- **命令 / 界面操作**：在初始 prompt 中加入 `{{ issue.description }}` 或等价值；把 `symphony-ready` 加入常规任务的 `required_labels`，多主机条件不得重叠。
- **确认结果**：完整 Issue body 进入 Codex 的初始 prompt，非目标 Issue 不被派发。
- **如果正常**：进入步骤 6。
- **如果异常**：修正 WORKFLOW、profile、adapter schema 和标签条件；不得只传 title。

### 6. 创建路由与状态标签

- **要执行的操作**：创建[状态标签](#状态标签)中列出的标签。
- **命令 / 界面操作**：使用 GitHub 标签界面或 `gh label create`。
- **确认结果**：获人工执行确认（Human GO）的 Issue 可同时添加 `symphony-ready` 和 `nd-status:scheduled`。
- **如果正常**：进入步骤 7。
- **如果异常**：检查标签名称、权限和 `required_labels`。

> **插图候选 3**：截取 Issue 同时显示 `symphony-ready` 与 `nd-status:scheduled`。应能区分两类标签；不要显示秘密、内部主机名或内部 URL。

### 7. 验证版本兼容性并执行冒烟验证

- **要执行的操作**：实测 approval policy、sandbox、tool schema 及完整配置。
- **命令 / 界面操作**：检查 adapter 连接、profile 加载、prompt、标签过滤、App Server、Git / PR 权限和非目标 Issue 不派发；在 Workpad 记录精确版本与结果。
- **确认结果**：所有项目通过，记录不含秘密信息。
- **如果正常**：进入步骤 8。
- **如果异常**：检查固定版本的 schema，不照搬其他版本；失败期间不要派发常规任务。

### 8. 执行第一个单任务端到端验证

- **要执行的操作**：在人工执行确认（Human GO）后，用区别于 bootstrap 的常规任务验证。
- **命令 / 界面操作**：完成 `ChatGPT → Issue → Symphony → Codex → 分支 / 验证 → PR → 人工审查`，把结果保存到 Workpad 和 PR。
- **确认结果**：可追踪完整 Issue body、变更、验证、PR 和审查状态。
- **如果正常**：进入常规运行。
- **如果异常**：检查 runtime log、Workpad、Git diff、验证和 PR；解决前不要派发更多任务。

只安装 Skill 并不代表运行环境安装完成。未安装主机的 bootstrap 必须在人工执行确认（Human GO）和 Issue 持久化后由人明确启动；这是有限例外，不是常规手动执行路径。

## 运行 / 常见问题

### Q. 什么时候使用 `@excellent-nd`？

A. 在新会话或 Skill 未自动选择时使用。同一会话已经启用后，无需每条消息都添加。

### Q. 可以只制定计划而不路由执行吗？

A. 可以。可整理计划、任务拆分、负责人、估算负载和执行目标候选；在人工执行确认（Human GO）前不创建或派发 Issue。

### Q. 常规流程是什么？

A. `ChatGPT → GitHub Issue → Symphony → Codex → PR → 人工审查 → merge → 结果拉取 → Issue close`。merge 后确认 Workpad、验证和剩余工作，再关闭 Issue。

> **插图候选 4**：截取 Issue、相关 PR 与审查关系。显示相互链接和审查状态；不要显示私有仓库名、私有分支名或含秘密的 diff / 日志。

### Q. Issue body 与 Codex prompt 有什么关系？

A. 完整 Issue body 就是 Execution Packet。adapter 把它规范化为 `issue.description`，WORKFLOW / profile 再渲染到 Codex 初始 prompt。

### Q. 如何拆分任务并分配 30:70 的负载？

A. 根据依赖、并行性和预估工时拆分为 1..N 个任务。30:70 表示估算总负载，不是任务数量比例。

### Q. `owner` 与 `execution_target` 有什么区别？

A. `owner` 是成果负责人，`execution_target` 是运行 Codex 的执行主机标识。目标未确定时不得派发。

### Q. 审查意见应写在 Chat、Issue 还是 PR？

A. 需求、优先级和人的判断写入 Chat；持久决策和阻塞项写入 Workpad；逐行意见写入 PR review。执行决定也同步到 Issue。

> **插图候选 5**：截取把 PR 意见带回 Chat 请求修改的示例。显示 PR 引用、修改要求和继续同一任务的意图；不要显示无关历史、个人信息、令牌或内部路径。

### Q. 如何处理 blocked 与 resume？

A. 把原因、依据和问题保存到 Workpad，将状态更新为 blocked 并停止派发。回答后把决定保存到 Issue，原则上继续同一 Issue 和 Codex thread。

### Q. 何时继续同一任务？

A. 目标和执行主机不变的修订继续同一任务。改变目标或主机时，创建带 checkpoint 的后继 Issue。

### Q. 如何拉取结果？

A. 在 Chat 中要求“拉取结果”，将 Workpad、PR、验证和 Git 状态合并回原计划。通常不拉取完整 Codex 日志。

### Q. Symphony 与 Codex 如何分工？

A. Symphony 编排 Issue 轮询、workspace、retry、thread / turn；Codex 执行仓库工作和验证。

### Q. `No queued retries` 是否表示成功？

A. 否。它只表示没有等待的 retry。还要检查 Issue 状态、runtime log、Workpad、commit / diff、验证和 PR。

## execution_target 方针

执行主机 hostname 是基本标识，在同一 LAN 或组织管理范围内必须唯一，并在 Issue 生命周期内保持不变。迁移时创建带 checkpoint 的后继 Issue。

如果公开内部 hostname 会泄露基础设施信息，应使用 `build-public-01` 等非敏感 hostname 或公开别名，并把映射保存在公开内容之外。不得改写现有 Issue 的 `execution_target`。

## 状态标签

| 标签 | 颜色 | 说明 |
| --- | --- | --- |
| `symphony-ready` | `0E8A16` | 路由 / 执行控制，不表示工作流状态 |
| `nd-status:scheduled` | `C2E0C6` | 已获人工执行确认，等待执行 |
| `nd-status:running` | `1D76DB` | Codex 正在执行 |
| `nd-status:blocked` | `D93F0B` | 等待人工判断、外部条件或额度 |
| `nd-status:review` | `FBCA04` | 等待人工审查 |
| `nd-status:failed` | `B60205` | 无法自动继续，需要检查原因 |

`nd-status:*` 原则上只激活一个。不要仅为显示 running 而移除 `symphony-ready`。用 `gh label create NAME --color HEX --description TEXT` 创建；用 GitHub UI 或 `gh label edit OLD --name NEW --color HEX --description TEXT` 修改。修改时同步 Skill、文档和自动处理；修改 `symphony-ready` 时同步所有 profile 的 `required_labels` 并重新冒烟验证。

Codex turn 前的失败有时没有自动更新主体。不得声称完全自动化；应根据 runtime log、Workpad 或结果拉取，由人或 ChatGPT 更新为 `failed` / `blocked`。

## 卸载

1. 在 ChatGPT Skill 管理中禁用或删除 `excellent-nd`。
2. 停止 Symphony runtime，并移除 systemd、container、login item 等自动启动。
3. 保留 host-local WORKFLOW / profile 以便回滚，或安全删除。
4. 停止 profile 后停止使用 `symphony-ready`，按需整理标签。
5. 在 provider 侧撤销 GitHub / Codex 凭据和令牌，并删除主机副本；不要记录值。
6. 确认审计与恢复要求后，按需删除 workspace、cache 和 log。
7. 原则上保留 Issue、PR、commit 和历史作为审计记录。

卸载 Excellent-Nd 不表示删除 Codex 或 GitHub 本身。

## 故障排查

Issue 未派发时，检查 GitHub native state、adapter 连接、profile 的 `required_labels`、`symphony-ready` 和执行目标条件。结果不明确时，依次检查 runtime log、Workpad、Git diff、验证和 PR。不要把秘密信息粘贴到诊断记录。
