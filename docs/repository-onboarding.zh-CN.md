# Repository / Issue 集成

Excellent-Nd 的安装分为三个层级：

1. 安装 ChatGPT Skill。
2. 将 Excellent-Nd 与目标仓库现有的 Issue 规则集成。
3. 安装执行主机 runtime。

第2层优先从 ChatGPT 完成。让 ChatGPT 检查现有 labels、Issue templates/forms、GitHub Actions/bot、status/routing 规则以及已有的 `.excellent-nd/repository.json`。

如果仓库没有冲突的 Issue 规则，可以采用标准 mapping。如果已有运用规则，ChatGPT 应一次性提出 mapping proposal 供确认，而不是要求人工逐个配置label。

只有确认语义一致时才复用既有label。`management: existing` 表示 Excellent-Nd 只验证存在，不创建或修改；`management: excellent-nd` 表示仅在缺失时创建，并且绝不覆盖同名既有label。

确认后的mapping保存在 `.excellent-nd/repository.json`。labels、Issue templates、automation 尚未确认时，execution-host setup 必须 fail closed。

ChatGPT 创建 Excellent-Nd Task 时会直接生成完整 Issue body，因此通常不需要修改既有 Issue template。


## 通用 mapping 与 dispatch gates

Excellent-Nd 不替换目标仓库原有的状态模型。Core 保持 `scheduled / running / blocked / review`，仓库特有的字段名和状态值全部通过配置适配。

`dispatch_gates[]` 可以组合 GitHub Project Field、label 和 Issue state。Agent、Human Approval 等字段只在需要它们的仓库中配置，不是 Excellent-Nd 的固定要求。

当 GitHub Project 是状态正本时，用 `status_integration.event_mapping` 将 Excellent-Nd runtime event 映射到仓库已有的状态值，并且只允许 `mutable_events` 中列出的事件自动更新。

公开通用示例为 `config/repository-config.github-project.example.json`。不要把 private repository 名称、内部 Project title 或可识别的工作流字段值复制到 public repository 的示例、Issue、PR 或 release artifact 中。
