# 使用指南

[日本語（正式规范）](operations.md) | [English](operations.en.md)

当前beta candidate为 `1.0.1`，已验证第一个常规single Task E2E。

## Installation

前提是可使用Skill/GitHub集成的ChatGPT、Issue/label/branch/PR最小权限，以及可运行已验证Symphony/Codex/Git组合的host。不要公开credential、token、private hostname或内部URL。

安装 `skills/excellent-nd/`（仅启用ChatGPT规则，不安装runtime）；准备GitHub认证并安全保存secret；按upstream安装并固定exact versions；配置GitHub Issues adapter，WORKFLOW/profile prompt须包含 `{{ issue.description }}`；required_labels使用 `symphony-ready` 并创建下列labels；验证approval policy/sandbox/tool schema版本兼容；smoke-test adapter/profile/prompt/filter/App Server/Git-PR权限/非目标不dispatch并记录结果；另用常规Task完成single Task E2E。bootstrap仅是Human GO和Issue记录下的限定例外。

## Operations / FAQ

新会话或Skill选择不明确时使用 `@excellent-nd`；同一会话已启用后无需每次添加。可只做Plan，但Human GO前不创建/routing Issue。流程为Plan/拆分/owner/负载/target → GO → Issue → Symphony → Codex → PR → Human review/merge → Result拉取 → close。完整Issue body是由 `issue.description` render的Execution Packet。

30:70是总负载估算而非Task数量。`owner` 是成果责任者，`execution_target` 是host identity；未确定target不得dispatch。需求/优先级/Human决定写Chat，持久决定/blocker写Issue Workpad，逐行意见写PR，并把执行决定同步到Issue。blocked时保存原因/问题并更新status/control；回答后优先继续同一Issue/thread。目标或host改变则建立带checkpoint的后继Issue。结果拉取读取Workpad/PR/verification/Git；merge后确认remaining work再close。

Symphony负责编排，Codex负责repository工作与验证。`No queued retries` 不是成功判定；共同检查Issue status、runtime log、Workpad、commit/diff、verification、PR。

## execution_target

默认使用同一LAN/组织范围唯一的hostname，Issue lifetime内不变；迁移用后继Issue。public repository中若private/internal hostname会泄露infra，使用 `build-public-01` 等non-sensitive hostname/public alias，mapping保存在公开artifact之外。不得改写现有Issue target。

## Labels

| Label | Color | Description |
| --- | --- | --- |
| `symphony-ready` | `0E8A16` | Routing / execution control; not workflow status |
| `nd-status:scheduled` | `C2E0C6` | Human GO complete; waiting to run |
| `nd-status:running` | `1D76DB` | Codex execution in progress |
| `nd-status:blocked` | `D93F0B` | Waiting for human, external condition, or quota |
| `nd-status:review` | `FBCA04` | Waiting for human review |
| `nd-status:failed` | `B60205` | Cannot continue automatically; inspect the cause |

用 `gh label create` 创建，以UI或 `gh label edit` 定制；status原则上只激活一个。rename时同步Skill/docs/automation。`symphony-ready` rename须同步所有profile的 `required_labels` 并smoke test。不要为显示running而切换routing label。Codex turn前failure可能无自动主体，应依据log/Workpad/Result由人或ChatGPT更新failed/blocked，不得声称全自动。

## Versioning

正式版 `X.Y`，beta/development版 `X.Y.Z`。`1.0.1` 是面向 `1.0` 的首个candidate。PR #7不建tag、不self-merge；Human merge后给main merge commit加 `1.0.1` tag作为release gate。

## Uninstall / disable

禁用/删除Skill；停止Symphony并移除auto-start；保留host-local WORKFLOW/profile用于rollback或安全删除；停止routing label并在profile停止后按需整理labels；在provider revoke GitHub/Codex credential/token并删除host副本，不记录值；确认审计/恢复要求后任意清理workspace/cache/log；原则上保留Issue/PR/commit/history。卸载Excellent-Nd不等于删除Codex或GitHub。
