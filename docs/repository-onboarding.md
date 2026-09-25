# Repository / Issue連携

Excellent-Ndの導入は次の3レベルで行う。

1. **Skill導入** — ChatGPTへexcellent-nd Skillを追加する。
2. **Repository / Issue integration** — 対象repositoryの既存Issue運用とExcellent-Ndを接続する。
3. **Execution host導入** — repository integration完了後にSymphony / Codex runtimeを設定する。

## ChatGPTからLevel 2を行う

手作業でlabelsやIssue templateを一つずつ設定するのではなく、まずChatGPTへ対象repositoryの導入を依頼する。

例:

> Excellent-Ndをこのrepositoryへ導入するため、既存Issue運用を監査し、repository integrationを設定してください。

ChatGPTは次を確認する。

- existing labelsと意味
- Issue templates / forms
- GitHub Actions / bot / automation
- status / routing convention
- 既存 `.excellent-nd/repository.json`

既存運用がない場合は標準mappingを利用できる。既存運用がある場合は、ChatGPTがmapping proposalをまとめて提示し、一度の確認後に設定する。

## 既存labelsの扱い

既存labelがExcellent-Nd semantic roleと同じ意味ならreuseできる。

例:

| Excellent-Nd role | 既存repository | 設定 |
| --- | --- | --- |
| routing | `ready-for-ai` | existing |
| running | `in-progress` | existing |
| blocked | `blocked` | existing |
| failed | なし | `nd-status:failed` を追加 |

名前が似ているだけではreuseしない。workflow triggerや既存botへの影響も確認する。

## Repository config

承認済み設定は `.excellent-nd/repository.json` に保存する。

このfileがlabel mapping、Issue template方針、automation review完了状態のSSOTとなる。

Execution-host setupはこのconfigがない場合に停止する。

## Label management

- `management: existing`: labelは既存repository管理。Excellent-Ndは存在確認のみ行い、作成・上書きしない。
- `management: excellent-nd`: 不足時だけ作成する。既存同名labelは上書きしない。

従来のsetupのように `--force` で既存label description/colorを変更しない。

## Issue templates

ChatGPTがExcellent-Nd Taskを作る場合はIssue bodyを直接生成するため、既存Issue template変更は通常不要。

方針:

- `preserve`: 既存templateを変更しない。標準。
- `customized`: manual Issue作成もExcellent-Nd形式へ合わせる等、明示的にcustomize済み。
- `not-used`: templateを利用しない。

## Automation

labelをtriggerにするGitHub Actionsやbotがある場合、mapping前に影響を確認する。

意味や影響が不明なら専用Excellent-Nd labelを追加する方が安全である。

## Execution host setup前Gate

以下すべてを満たすまでLevel 3へ進まない。

- repository config exists
- labels reviewed
- Issue templates reviewed
- automation reviewed
- existing-managed labels exist
- repository config validation PASS

```bash
python3 scripts/repository_config.py validate --repo-root .
```

詳しい仕様はSkillの `references/repository-onboarding.md` を参照する。
