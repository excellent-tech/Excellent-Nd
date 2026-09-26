# 使用指南

[日本語（规范原文）](operations.md) | [English](operations.en.md)

本指南面向安装、运行和停用 Excellent-Nd 的操作者。版本编号规则和当前候选版本请参阅[版本方针](../skills/excellent-nd/references/version-policy.md)。


## 三层安装

Excellent-Nd 按 **Skill → Repository / Issue 集成 → Execution host** 的顺序配置。参阅 [Repository / Issue 集成](repository-onboarding.zh-CN.md)。

在 `.excellent-nd/repository.json` 确认 labels、Issue templates 与 automation 的审查完成之前，不进入执行主机安装。优先让 ChatGPT 审计仓库并提出mapping方案。

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

### 3. 配置 Repository / Issue 集成

- **要执行的操作**：配置目标仓库与认证。
- **命令 / 界面操作**：通过 GitHub App 或官方集成授予 Issue、标签、分支和 PR 所需的最小权限，把秘密值保存在密钥存储中。
- **确认结果**：可以读写测试 Issue，并执行所需的分支和 PR 操作。
- **如果正常**：进入步骤 4。
- **如果异常**：修正安装范围、权限和仓库选择；不要把秘密值贴到 Issue 或日志。

### 4. 获取已验证的 runtime

- **操作**: 获取 manifest 固定的 upstream Symphony。
- **命令 / UI 操作**: 运行 `python3 scripts/setup.py --repo OWNER/REPOSITORY --prefix .excellent-nd --skill-confirmed`，并将 `.excellent-nd/` 放在 Git 管理之外。
- **确认结果**: asset 与 `config/runtime-lock.json` 的 SHA-256 一致。
- **OK**: 进入步骤 5。
- **NG**: 检查 platform、release asset 和网络；checksum 不一致时停止。

### 5. 确认 Codex App Server 兼容性

- **操作**: 确认 Codex version 与 approval / sandbox policy。
- **命令 / UI 操作**: 运行 `codex --version`；setup 检查 exact version 和 `approval_policy: never`。
- **确认结果**: 与 manifest 一致且 App Server 可用。
- **OK**: 进入步骤 6。
- **NG**: 不要套用其他 version 的配置；验证完成前停止。

### 6. 确认 WORKFLOW 与 GitHub Issues adapter

- **操作**: 检查 `.excellent-nd/WORKFLOW.md`。
- **命令 / UI 操作**: 确认 repository、`required_labels: symphony-ready`、`{{ issue.description }}`、workspace 和 Codex policy。
- **确认结果**: 完整 Issue body 进入首个 prompt，不调度不合格 Issue。GitHub adapter 使用 host-side `before_run` hook 在 Codex sandbox 外把 clean workspace 刷新到远端默认分支；Codex 在 `workspace-write` 下保持 `.git` 受保护，只进行只读 Git 验证，并通过 host-side `github_api` 发布 branch / commit / Draft PR。
- **OK**: 进入步骤 7。
- **NG**: 修正 template 后重新生成，不使用只传 title 的 profile。

### 7. 确认路由与状态标签

- **操作**: 检查 setup 创建或更新的 label。
- **命令 / UI 操作**: 在 GitHub 确认 `symphony-ready` 和五个 `nd-status:*`。
- **确认结果**: 路由与可视化职责分离。
- **OK**: 进入步骤 8。
- **NG**: 使权限、名称和 profile `required_labels` 一致。

> **插图候选 3**：能区分 `symphony-ready` 与 `nd-status:scheduled` 的 Issue 画面。不要显示秘密或非公开 hostname / URL。

### 8. 通过 observer 启动 Symphony

- **操作**: 在同一 process tree 中启动 observer 与 Symphony。
- **命令 / UI 操作**: 在步骤4的setup command后增加 `--start`。
- **确认结果**: observer 转发 stdout / stderr，runtime 持续运行。
- **OK**: 进入步骤 9。
- **NG**: 检查 binary、profile、认证和log；不新增 scheduler 或 polling daemon。

> **插图候选 2**：只显示正常进程和profile已读取。不要显示 token、非公开 hostname / path、环境变量值或内部 URL。

### 9. 执行冒烟验证

- **操作**: 确认 deterministic preflight 与 live runtime。
- **命令 / UI 操作**: 必要时重新运行 `python3 scripts/smoke.py --runtime .excellent-nd/symphony --workflow .excellent-nd/WORKFLOW.md --repo OWNER/REPOSITORY`，并从log确认没有误调度。
- **确认结果**: `readiness: PASS`、正常启动且无误调度。
- **OK**: 进入步骤 10。
- **NG**: 不要添加 routing label；修正 checksum、Codex version、GitHub auth 或 WORKFLOW。

### 10. 将 readiness 保存到 Workpad

- **操作**: 把实测version、profile revision、验证和剩余风险保存到bootstrap Issue。
- **命令 / UI 操作**: 只comment已清理秘密的结果。
- **确认结果**: 仅凭Issue可判断是否能开始E2E。
- **OK**: 进入步骤 11。
- **NG**: 保持普通Task不可调度。

### 11. 执行第一个单任务端到端验证

- **操作**: 仅在当前user message同时含 `@excellent-nd` 与人工执行确认（Human GO）时执行普通Task。
- **命令 / UI 操作**: 完成 `ChatGPT → Issue → Symphony → Codex → branch / verification → PR → 人工审查`。
- **确认结果**: 变更、验证和PR可追踪；进入review时同一decision移除routing label。
- **OK**: 进入常规运行。
- **NG**: 检查log、Workpad、diff、验证和PR；解决前不调度更多Task。
只安装 Skill 并不代表运行环境安装完成。未安装主机的 bootstrap 必须在人工执行确认（Human GO）和 Issue 持久化后由人明确启动；这是有限例外，不是常规手动执行路径。

## 运行 / 常见问题

### Q. 什么时候使用 `@excellent-nd`？

A. 每次请求 Codex dispatch 的当前 user message 都必须明确包含它（不区分大小写），同一决策上下文还必须有人工执行确认（Human GO）。Skill 自动选择或只满足一个 gate 时，仅进行计划、调查和可由 ChatGPT 安全完成的 GitHub 操作，不添加或恢复 `symphony-ready`。

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

## 运行中断记录与恢复

observer在同一Symphony process tree中跟随observable event。只有带Issue context的使用额度耗尽、长时间rate limit、turn timeout、App Server启动失败或agent abnormal exit，才会把已清理秘密和非公开path的category、error、occurred_at、可取得的reset / retry与session / attempt、checkpoint可取得性、剩余工作和恢复条件写入Workpad。短周期retry交给Symphony，不创建comment。缺少Issue编号或准确error时标为无法取得，不作推测。

中断时在同一次Issue更新中设置 `workflow_status=blocked`、`nd-status:blocked` 并移除 `symphony-ready`。进入review时也在同一decision移除routing。仅在当前user message再次包含 `@excellent-nd` 与人工执行确认（Human GO）后恢复。

```sh
python3 scripts/runtime_observer.py resume --repo OWNER/REPOSITORY --issue NUMBER \\
  --reason "resume condition verified" --explicit-mention --human-go
```

该操作保存决策并恢复 `scheduled`、`nd-status:scheduled` 与routing。优先同一Issue / thread，不进行无条件自动重新调度。

## 多执行主机的注册与删除

注册时机、多主机追加、临时停用、删除和重新注册请参阅 [execution_target 与执行主机台账](execution-targets.zh-CN.md)。

要点是：setup仅在冒烟验证PASS后生成本地台账file；该file commit并merge后，共享注册才生效。删除顺序为 `disable → drain/迁移active Task → 删除target file`。
\n\n## execution_target 方针

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

Issue 未派发时，检查 GitHub native state、adapter 连接、profile 的 `required_labels`、`symphony-ready` 和执行目标条件。结果不明确时，依次检查 runtime log、Workpad、Git diff、验证和 PR。Codex `workspace-write` 会有意保护 `.git` 不可写；遇到 `FETCH_HEAD`、branch 或 commit 写入失败时，不要通过修改 ownership / permissions 或启用 `danger-full-access` 绕过。clean workspace 由 host-side `before_run` hook 刷新，GitHub 发布使用 Symphony host-side `github_api`。不要把秘密信息粘贴到诊断记录。
