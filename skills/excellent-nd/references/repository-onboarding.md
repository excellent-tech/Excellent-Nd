# Repository / Issue integration

Excellent-Nd導入のLevel 2。execution host setupより先に、対象repositoryの既存Issue運用とExcellent-Ndのsemantic rolesを整合させる。

## 目的

既存repositoryにあるlabels、Issue templates、GitHub Actions、bot、自動化を壊さず、Excellent-Ndが必要なrouting/status semanticsだけを安全に接続する。

## ChatGPTからの推奨フロー

### 1. Repositoryを特定する

対象 `OWNER/REPOSITORY` を確認する。

### 2. 現状を監査する

ChatGPTから可能な範囲で次を読む。

- existing labels: name / description / 実際の使用例
- `.github/ISSUE_TEMPLATE/**`
- issue forms / config
- `.github/workflows/**`
- bot / automation設定
- README / contributing等のIssue運用記述
- `.excellent-nd/repository.json`

特にlabelをtriggerにするautomationを探す。

### 3. semantic mappingを作る

Excellent-Ndが必要とするroles:

- routing
- status: scheduled
- status: running
- status: blocked
- status: review
- status: failed
- execution target prefix

各roleごとに:

- `management: existing`: 既存運用のlabelをそのまま使う。setupは存在確認だけ行う。
- `management: excellent-nd`: Excellent-Nd側で利用するlabel。setupは不足時だけ作成する。

既存labelと意味が完全に一致すると確認できた場合だけ `existing` としてreuseする。

名前が似ているだけ、descriptionが空、automation影響が不明な場合は自動reuseしない。専用labelを追加する方が安全である。

### 4. Issue template方針を決める

`.excellent-nd/repository.json` の `issue_templates.policy`:

- `preserve`: 既存templateを変更しない。標準推奨。
- `customized`: manual Issue作成もExcellent-Nd形式へ合わせる等、別途customize済み。
- `not-used`: repositoryでIssue templateを利用しない。

ChatGPTがExcellent-Nd Taskを作る場合はIssue bodyを直接生成するため、template変更は通常不要。

### 5. automationとの矛盾を確認する

次を確認する。

- mapped labelを付けたとき既存workflowが意図せず動かないか
- existing status automationとExcellent-Nd observerが同じlabelを競合更新しないか
- Issue close/reopen botがterminal semanticsと衝突しないか
- routing labelを外すreview/blocked処理と既存automationが矛盾しないか

不明点がある場合、`reviewed.automation=true` にしない。

### 6. Proposalを確認する

既存運用がある場合、ChatGPTは変更前に表形式等で以下を提示する。

- semantic role
- proposed label
- existing / excellent-nd management
- evidence / existing rule
- change required
- conflict/risk

一度の確認でmapping全体を承認できるようにし、個別ラベルごとの手作業確認を要求しない。

### 7. Repository configを保存する

承認後、`.excellent-nd/repository.json` を作成・更新する。

例:

```json
{
  "schema": "excellent-nd/repository@v1",
  "issue_integration": {
    "reviewed": {
      "labels": true,
      "issue_templates": true,
      "automation": true
    },
    "issue_templates": {
      "policy": "preserve"
    },
    "labels": {
      "routing": {
        "name": "ready-for-ai",
        "management": "existing"
      },
      "status": {
        "scheduled": {
          "name": "nd-status:scheduled",
          "management": "excellent-nd"
        },
        "running": {
          "name": "in-progress",
          "management": "existing"
        },
        "blocked": {
          "name": "blocked",
          "management": "existing"
        },
        "review": {
          "name": "review",
          "management": "existing"
        },
        "failed": {
          "name": "nd-status:failed",
          "management": "excellent-nd"
        }
      },
      "target": {
        "prefix": "nd-target:",
        "management": "excellent-nd"
      }
    }
  }
}
```

### 8. Label変更を適用する

- existing-managed labelは作成・rename・description/color変更をしない。
- excellent-nd-managed labelは不足時だけ作成する。
- 同名labelが既に存在する場合は上書きしない。
- 既存labelのrename/deleteはrepository integrationの自動処理に含めない。

### 9. Validation

```bash
python3 scripts/repository_config.py validate --repo-root .
```

PASS後にLevel 3 execution-host setupへ進む。

## Clean repository

既存Issue運用やlabel automationがないrepositoryでは標準configを利用できる。

```bash
python3 scripts/repository_config.py init-standard --repo-root .
```

ただしChatGPT導入では、可能な限り先にrepositoryを監査し、競合がないことを確認してから標準configをcommitする。

## 既存ルールとの関係

Excellent-Ndは既存Issue process全体を置換しない。

必要なのはExcellent-Ndのsemantic rolesをrepository側の実際のlabelsへmappingすることだけである。既存のbug/feature/priority/team labels等はそのまま共存できる。

## Fail closed

次の場合はexecution host setupへ進まない。

- repository configがない
- labels / templates / automationのreview済みflagがfalse
- existing-managed labelが存在しない
- semantic rolesが同じlabelへ重複mappingされている
- target prefixが不正
