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
