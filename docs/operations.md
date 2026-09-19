# 利用ガイド

[简体中文](operations.zh-CN.md) | [English](operations.en.md)

日本語を正本とする。現在のbeta candidateは `1.0.1` で、最初の通常single Task E2Eまで実証済みである。

## Installation

前提は、Skill/GitHub連携を使えるChatGPT、Issue/label/branch/PRの最小権限を持つrepository認証、検証済みSymphony・Codex CLI/App Server・Gitを動かせるexecution hostである。credential、token、private hostname、内部URLをpublic artifactへ書かない。

1. `skills/excellent-nd/` をChatGPT Skillとして導入する。これはChatGPT側の操作規約だけで、runtime導入完了ではない。
2. GitHub repositoryと認証を準備し、secret値はhostのsecret store等に置く。
3. upstream手順でSymphony/Codex App Serverをhostへ導入し、検証済みexact version setを固定する。
4. GitHub Issues adapterを設定する。WORKFLOW/profileのinitial promptへ `{{ issue.description }}` または同等値を含め、Issue body全体を渡す。
5. profileの `required_labels` に `symphony-ready` を設定し、下記status labelsを作る。複数hostでは重複dispatchしない条件を検証する。
6. approval policy、sandbox、tool schemaはversion依存である。別versionの例を流用せず、固定versionのschemaとsmoke testで確認する。
7. adapter接続、profile読込、prompt、label filter、App Server、Git/PR権限、非対象Issueの非dispatchをsmoke verificationし、exact versionsと結果をWorkpadへ残す。
8. 別の通常Taskで `ChatGPT → Issue → Symphony → Codex → branch/verification → PR → Human review` を通す。bootstrap Issueは代用しない。

未導入hostのbootstrapはHuman GOとIssue永続化後に人間が明示開始する限定例外で、通常Taskのmanual経路ではない。

## Operations / FAQ

- `@excellent-nd`: 新規会話やSkillが自動選択されない時に付ける。同じ会話で有効なら毎回不要。付けずにPlanだけ作れるが、Human GOなしにIssue作成/routingしない。
- 通常フロー: Plan/Task分割/owner/負荷/target案 → Human GO → Issue → Symphony → Codex → PR → Human review/merge → Result取り込み → Issue close。
- Issue body全体がExecution Packetで、runtimeは `issue.description` としてinitial promptへrenderする。
- 30:70は件数比でなく依存・並列性・工数を含む概算総負荷。
- `owner` は成果責任者、`execution_target` はCodexを動かすhost。target未確定ならdispatchableにしない。
- review指摘: 要件・優先順位・Human判断はChat、永続判断/blockerはIssue Workpad、行単位diffはPR。実行に必要な決定はIssueにも反映する。
- blocked: 理由と質問をIssueへ保存しstatus/controlを更新する。回答後は同じIssue/threadのcontinuationを優先する。目的またはhost変更時はcheckpoint付き後継Issueを作る。
- 「結果を取り込んで」でWorkpad、PR、verification、Git状態をPlanへ統合する。merge後もResult/remaining workを確認してcloseする。
- Symphonyはpolling/workspace/retry/threadをorchestrateし、Codexはrepository作業と検証を行う。
- `No queued retries` はretry queueの状態であり成功判定ではない。Issue status、runtime log、Workpad、commit/diff、verification、PRを合わせて確認する。

## execution_target

execution hostのhostnameを基本identityとし、同一LAN/組織管理範囲で一意、Issue lifetime中は不変とする。host移行は後継Issueを作る。public repositoryでprivate/internal hostnameがinfra情報を漏らす場合は `build-public-01` のようなnon-sensitive hostname/public aliasを使い、mappingは公開artifact外に保持する。既存Issueのtargetは変更しない。

## Labels

| Label | Color | Description |
| --- | --- | --- |
| `symphony-ready` | `0E8A16` | Routing / execution control; not workflow status |
| `nd-status:scheduled` | `C2E0C6` | Human GO complete; waiting to run |
| `nd-status:running` | `1D76DB` | Codex execution in progress |
| `nd-status:blocked` | `D93F0B` | Waiting for human, external condition, or quota |
| `nd-status:review` | `FBCA04` | Waiting for human review |
| `nd-status:failed` | `B60205` | Cannot continue automatically; inspect the cause |

`gh label create NAME --color HEX --description TEXT` で作成し、GitHub UIまたは `gh label edit OLD --name NEW --color HEX --description TEXT` でcustomizeできる。status labelは原則1つ。rename時はSkill/docs/automationを同期する。`symphony-ready` のrenameは全profileの `required_labels` を同時更新しsmoke testする。running中にstatus表示目的でrouting labelを外さない。Codex turn開始前のfailure等は自動更新主体がないため自動化済みとせず、log/Workpad/Result取り込みを根拠に人間またはChatGPTがfailed/blockedを更新する。

## Versioning

正式版は `X.Y`、beta/development版は `X.Y.Z`。`1.0.1` は `1.0` に向けた最初のcandidate。PR #7ではtag作成/self-mergeせず、Human merge後にmainのmerge commitへ `1.0.1` tagを付けることをrelease gateとする。

## Uninstall / disable

1. ChatGPT Skillを無効化/削除する。
2. Symphonyを停止しsystemd/container/login item等のauto-startを解除する。
3. host-local WORKFLOW/profileをrollback用に保管または安全に削除する。
4. routing label運用を止め、profile停止後にlabelsを任意整理する。
5. GitHub/Codex credential/tokenをprovider側でrevokeしhostから消す。値は記録しない。
6. audit/recovery要件確認後にworkspace/cache/logを任意cleanupする。
7. Issue/PR/commit/historyは監査記録として原則保持する。

Excellent-NdのuninstallはCodex/GitHub自体の削除を意味しない。
