# 利用ガイド

[简体中文](operations.zh-CN.md) | [English](operations.en.md)

このガイドは、Excellent-Nd を導入・運用・停止する作業者向けの手順書です。バージョン番号の規則と現在の候補版は[バージョン方針](../skills/excellent-nd/references/version-policy.md)を参照してください。


## 導入の3レベル

Excellent-Ndは **Skill導入 → Repository / Issue連携 → Execution host導入** の順で設定する。Level 2の詳細は [Repository / Issue連携](repository-onboarding.md) を参照する。

Execution host setupは `.excellent-nd/repository.json` がreview済みでない場合は開始しない。既存labelsやautomationがあるrepositoryでは、ChatGPTに監査とmapping proposal作成を依頼し、確認後に設定する。

## インストール

### 1. 前提条件を確認する

- **操作すること**: ChatGPT、GitHub リポジトリ、実行ホストを準備する。
- **コマンド / UI 操作**: ChatGPT で Skill と GitHub 連携を利用できること、GitHub で Issue・ラベル・ブランチ・PR を操作できること、実行ホストで Git を利用できることを確認する。
- **確認する結果**: 必要な最小権限があり、認証情報を秘密情報ストア等へ保存できる。
- **OK の場合**: 手順 2 へ進む。
- **NG の場合**: 権限と認証情報の保管方法を整えるまで導入を中止する。認証情報、トークン、非公開ホスト名、内部 URL は公開物へ記載しない。

### 2. excellent-nd Skill を導入する

- **操作すること**: リポジトリの `skills/excellent-nd/` を ChatGPT 側へ導入する。
- **コマンド / UI 操作**: ChatGPT の Skill 管理画面で追加し、有効化する。
- **確認する結果**: Skill 一覧に `excellent-nd` が表示され、選択できる。
- **OK の場合**: 手順 3 へ進む。
- **NG の場合**: Skill の配置、権限、メタデータを確認し、解消するまで実行環境の設定へ進まない。

> **挿図候補 1**: ChatGPT の Skill 一覧で `excellent-nd` を選択できる画面を撮る。名称と有効状態が見えていればよい。会話内容、トークン、アカウント情報、非公開 URL は写さない。

### 3. Repository / Issue連携をChatGPTから設定する

- **操作すること**: 対象repositoryの認証を確認し、既存labels、Issue templates/forms、GitHub Actions/botを監査して `.excellent-nd/repository.json` を作成・確認する。
- **コマンド / UI 操作**: GitHub App または公式連携へ、Issue・ラベル・ブランチ・PR に必要な最小権限を与える。秘密値はホストの秘密情報ストアへ保存する。
- **確認する結果**: GitHub操作権限があり、labels / templates / automationのreviewが完了し、承認済みlabel mappingが `.excellent-nd/repository.json` に保存される。
- **OK の場合**: 手順 4 へ進む。
- **NG の場合**: 権限または既存Issue運用との矛盾を解消する。意味不明な既存labelを名前だけでreuseせず、Level 3へ進まない。

### 4. 検証済み runtime を取得する

- **操作すること**: manifest に固定された upstream Symphony を取得する。
- **コマンド / UI 操作**: `python3 scripts/setup.py --repo OWNER/REPOSITORY --repo-path . --prefix .excellent-nd --skill-confirmed` を実行するとlocal hostnameをtarget IDの既定値にする。hostnameをrepositoryへ載せたくない場合だけ `--execution-target build-public-01` のようなaliasを指定する。`.excellent-nd/targets/*.json` はGit管理し、それ以外の `.excellent-nd/` runtime stateはGit管理外にする。
- **確認する結果**: `config/runtime-lock.json` の対象 asset と SHA-256 が一致し、host-local `.excellent-nd/host.json` とrepository台帳 `.excellent-nd/targets/<target-id>.json` にtarget identityが保存される。
- **OK の場合**: 手順 5 へ進む。
- **NG の場合**: platform、release asset、network を確認し、checksum 不一致なら中止する。

### 5. Codex App Server の互換性を確認する

- **操作すること**: Codex version と approval / sandbox policy を確認する。
- **コマンド / UI 操作**: `codex --version` を実行する。setup は exact version と `approval_policy: never` を検査する。
- **確認する結果**: manifest と一致し、App Server が利用できる。
- **OK の場合**: 手順 6 へ進む。
- **NG の場合**: 別 version の設定を流用せず、検証完了まで中止する。

### 6. WORKFLOW と GitHub Issues adapter を確認する

- **操作すること**: 生成された `.excellent-nd/WORKFLOW.md` を確認する。
- **コマンド / UI 操作**: repository、`required_labels` にrepository configで承認されたrouting labelとこのhostのtarget labelがあること、`{{ issue.description }}`、workspace、Codex policy を確認する。
- **確認する結果**: Issue body 全体が最初の prompt へ渡り、対象外 Issue は配信されない。GitHub adapterでは、clean workspaceを`before_run` hookがCodex sandbox外でremote default branchへ更新し、Codexは`workspace-write`の`.git`保護を維持したままread-only Git検証とhost-side `github_api`によるbranch / commit / Draft PR作成を行う。
- **OK の場合**: 手順 7 へ進む。
- **NG の場合**: template を修正して再生成する。title だけを渡す profile は使わない。

### 7. routing と状態authorityを確認する

- **操作すること**: repository configのstatus authorityと、setupが作成したexecution-control metadataを確認する。
- **コマンド / UI 操作**: label authorityではconfigured status labelsを確認する。GitHub Project authorityではrouting / target labelだけを確認し、`python3 scripts/repository_adapter.py --repository-config .excellent-nd/repository.json preflight --repo OWNER/REPOSITORY --issue ISSUE_NUMBER` でrepository固有のgeneric dispatch gatesを検証する。Agent / Human Approval等は設定された場合だけ評価する。
- **確認する結果**: status authorityが既存repositoryの正本と一致し、Project authorityでは`nd-status:*`が作成されていない。
- **OK の場合**: 手順 8 へ進む。
- **NG の場合**: 権限、名称、profile の `required_labels` を一致させる。

> **挿図候補 3**: `symphony-ready` と `nd-status:scheduled` が区別できる Issue 画面。秘密、非公開 hostname / URL は写さない。

### 8. Symphony を observer 経由で起動する

- **操作すること**: Symphony と同じ process tree の observer を起動する。
- **コマンド / UI 操作**: 手順4のsetup commandへ `--start` を追加する。現在のSymphony preview runtimeがguardrails acknowledgementを要求する場合は、人間が警告内容を確認したうえで `--i-understand-that-this-will-be-running-without-the-usual-guardrails` も明示する。Excellent-Ndはこの明示指定がある場合だけupstream Symphonyへ同じacknowledgement flagを転送する。
- **確認する結果**: observer が stdout / stderr を転送し、runtime が継続稼働する。
- **OK の場合**: 手順 9 へ進む。
- **NG の場合**: binary、profile、認証、process log を確認する。別 scheduler / polling daemon は追加しない。

> **挿図候補 2**: 正常稼働とprofile読込だけが見える画面。token、非公開 hostname / path、環境変数、内部 URL は写さない。

### 9. smoke verification を実施する

- **操作すること**: deterministic preflight と live runtime を確認する。
- **コマンド / UI 操作**: 必要なら `python3 scripts/smoke.py --runtime .excellent-nd/symphony --workflow .excellent-nd/WORKFLOW.md --repo OWNER/REPOSITORY --execution-target TARGET_ID` を再実行し、誤配信がないことをlogで確認する。
- **確認する結果**: `readiness: PASS`、正常起動、誤配信なし。
- **OK の場合**: 手順 10 へ進む。
- **NG の場合**: routing labelを付けず、checksum、Codex version、GitHub auth、WORKFLOWを修正する。

### 10. readiness を Workpad へ保存する

- **操作すること**: 実測version、profile revision、検証、残riskをbootstrap Issueへ保存する。
- **コマンド / UI 操作**: 秘密値を除いた結果だけをcommentする。
- **確認する結果**: IssueだけでE2E開始可否を判断できる。
- **OK の場合**: 手順 11 へ進む。
- **NG の場合**: 不足を解消するまで通常Taskをdispatchableにしない。

### 11. 最初の single Task E2E を実施する

- **操作すること**: 現在のuser messageに `@excellent-nd` と人間による実行承認（Human GO）が両方ある場合だけ通常Taskを実行する。
- **コマンド / UI 操作**: `ChatGPT → Issue → Symphony → Codex → branch / verification → PR → 人間レビュー` を通す。
- **確認する結果**: 変更・検証・PRを追跡でき、review遷移と同時にrouting labelが外れる。
- **OK の場合**: 通常運用へ進む。
- **NG の場合**: runtime log、Workpad、diff、検証、PRを確認し、解消まで追加Taskを配信しない。
Skill の導入だけでは実行環境の導入は完了しない。未導入ホストの bootstrap は、人間による実行承認（Human GO）と Issue 永続化の後に人間が明示的に開始する限定例外であり、通常タスクの手動実行経路ではない。

## 運用 / よくある質問

### Q. `@excellent-nd` はいつ付けますか？

A. Codex dispatchを要求する現在のuser messageに毎回明示します（大文字・小文字は区別しません）。同じ決定文脈に人間による実行承認（Human GO）も必要です。Skillの自動選択または片方のgateだけでは、ChatGPT内の計画・調査・安全なGitHub操作までとし、`symphony-ready`を追加・復元しません。

### Q. 計画だけを作り、実行へ routing しないことはできますか？

A. できます。計画、タスク分割、担当者、概算負荷、実行先候補まで整理し、人間による実行承認（Human GO）が出るまで Issue の作成や配信を行いません。

### Q. 通常の流れは何ですか？

A. `ChatGPT → GitHub Issue → Symphony → Codex → PR → 人間レビュー → merge → 結果取り込み → Issue close` です。merge 後も Workpad、検証結果、残作業を確認してから Issue を閉じます。

> **挿図候補 4**: GitHub 上で Issue、関連 PR、レビューの関係が分かる画面を撮る。Issue と PR の相互リンクとレビュー状態が見えていればよい。非公開リポジトリ名、非公開ブランチ名、秘密を含む差分やログは写さない。

### Q. Issue body と Codex の prompt はどう関係しますか？

A. Issue body 全体が Execution Packet です。adapter が `issue.description` へ正規化し、WORKFLOW / profile が Codex の最初の prompt へ描画します。

### Q. タスク分割と 30:70 の負荷配分はどう扱いますか？

A. 依存関係、並列可能性、想定工数を基に 1..N タスクへ分割します。30:70 は件数比ではなく、概算の総負荷比です。

### Q. `owner` と `execution_target` の違いは何ですか？

A. `owner` は成果の責任者、`execution_target` は Codex を動かす実行ホストの安定IDです。非公開repositoryではinstall時hostnameを既定値にでき、public repositoryではpublic-safe aliasを使います。通常Taskは `symphony-ready` と `nd-target:<execution_target>` の両方が揃ったときだけ該当hostへ配信します。実行先が未確定なら Issue を配信可能にしません。

### Q. レビュー指摘は Chat、Issue、PR のどこへ書きますか？

A. 要件、優先順位、人間の判断は Chat、永続的な判断と blocker は Issue Workpad、行単位の差分指摘は PR review に書きます。実行に必要な決定は Issue にも反映します。

> **挿図候補 5**: PR の指摘を Chat へ戻して修正を依頼する例を撮る。PR 参照、修正指示、同じタスクを継続する意図が見えていればよい。会話履歴の不要部分、個人情報、トークン、非公開パスは写さない。

### Q. blocked と resume はどう扱いますか？

A. 理由、根拠、質問を Workpad へ保存し、`workflow_status` と可視化ラベルを blocked に更新して配信を止めます。回答後は決定を Issue へ保存し、原則として同じ Issue と Codex thread を再開します。

### Q. 同じタスクの continuation と別タスクの境界は何ですか？

A. 目的と実行ホストが同じ修正は同じタスクを継続します。目的またはホストを変える場合は checkpoint を持つ後継 Issue を作ります。

### Q. 結果はどう取り込みますか？

A. Chat で「結果を取り込んで」と指示し、Issue Workpad、PR、検証、Git 状態を元の計画へ統合します。Codex の全文ログは通常取り込みません。

### Q. Symphony と Codex の役割は何ですか？

A. Symphony は Issue 監視、workspace、retry、thread / turn を編成します。Codex はリポジトリの作業と検証を実行します。

### Q. `No queued retries` は成功を意味しますか？

A. いいえ。retry queue に待機がないことだけを示します。Issue 状態、runtime log、Workpad、commit / diff、検証、PR を合わせて確認します。

## 実行中断の記録と再開

observerはSymphonyの同一process treeでobservable eventを監視します。Issue contextを持つ利用枠超過、長時間rate limit、turn timeout、App Server起動失敗、agent abnormal exitだけを、秘密情報と非公開pathを除去してWorkpadへ保存します。category、error、occurred_at、取得可能なreset / retryとsession / attempt、checkpoint取得可否、残作業、再開条件を記録します。短周期retryはSymphonyへ委ね、commentを作りません。Issue番号や正確なerrorがeventにない場合は推測せず、取得不能とします。

中断時はIssue bodyの `workflow_status=blocked`、`nd-status:blocked`、`symphony-ready`削除を同じIssue更新で行います。review遷移でもrouting labelを同時に外します。再開は現在のuser messageで `@excellent-nd` と人間による実行承認（Human GO）を再確認してから行います。

```sh
python3 scripts/runtime_observer.py resume --repo OWNER/REPOSITORY --issue NUMBER \\
  --reason "resume condition verified" --explicit-mention --human-go
```

決定理由をWorkpadへ保存し、`scheduled`、`nd-status:scheduled`、routing labelを復元します。同一Issue / threadを優先し、無条件の自動再dispatchは行いません。

## 複数作業マシンの登録・削除

登録タイミング、複数host追加、一時無効化、削除、再登録の詳細は [execution_target と作業マシン台帳](execution-targets.md) を参照してください。

要点は、**smoke PASS後にローカル台帳fileを生成し、そのfileをcommit / mergeした時点で共有登録が成立する**ことです。削除は `disable → active Taskのdrain / 移行 → target file削除` の順序で行います。
\n\n## execution_target 方針

実行ホストの hostname を基本識別子とし、同一 LAN または組織の管理範囲で一意にします。Issue の存続期間中は変更せず、ホスト移行時は checkpoint を持つ後継 Issue を作ります。

公開リポジトリで非公開・内部 hostname がインフラ情報を漏らす場合は、`build-public-01` のような機密でない hostname または公開 alias を使い、対応表を公開物の外に保持します。既存 Issue の `execution_target` は書き換えません。

## ステータス表現\n\n`status_integration.authority=labels` のrepositoryでは以下のstatus labelsを利用できる。`authority=github-project` では既存Project Fieldが正本であり、`nd-status:*`を生成しない。\n\n### Label authority

| ラベル | 色 | 説明 |
| --- | --- | --- |
| `symphony-ready` | `0E8A16` | Task routing / 実行制御。ワークフロー状態ではない |\n| `nd-target:<target-id>` | `5319E7` | host-specific routing。setup時にtargetごとに作成 |
| `nd-status:scheduled` | `C2E0C6` | 人間による実行承認済み、実行待ち |
| `nd-status:running` | `1D76DB` | Codex が実行中 |
| `nd-status:blocked` | `D93F0B` | 人間判断、外部条件、利用枠を待機中 |
| `nd-status:review` | `FBCA04` | 人間レビュー待ち |
| `nd-status:failed` | `B60205` | 自動継続できない失敗。原因確認が必要 |

`nd-status:*` は原則 1 つだけ有効にします。running の表示だけを目的に `symphony-ready` を外しません。

作成例:

```sh
gh label create symphony-ready --color 0E8A16 --description "Routing / execution control"
gh label create "nd-status:scheduled" --color C2E0C6 --description "人間による実行承認済み、実行待ち"
gh label create "nd-status:running" --color 1D76DB --description "Codex execution in progress"
gh label create "nd-status:blocked" --color D93F0B --description "Waiting for human, external condition, or quota"
gh label create "nd-status:review" --color FBCA04 --description "Waiting for human review"
gh label create "nd-status:failed" --color B60205 --description "Cannot continue automatically; inspect the cause"
```

GitHub UI または `gh label edit OLD --name NEW --color HEX --description TEXT` で名称・色・説明を変更できます。変更時は Skill、文書、自動処理を同期します。`symphony-ready` を変更する場合は全 profile の `required_labels` を同時に更新し、smoke test を再実施します。

Codex turn 前の失敗などは、自動更新する主体が存在しない場合があります。完全自動化済みとは扱わず、runtime log、Workpad、結果取り込みを根拠に、人間または ChatGPT が `failed` / `blocked` へ更新します。

## アンインストール

1. ChatGPT の Skill 管理画面で `excellent-nd` を無効化または削除する。
2. Symphony runtime を停止し、systemd、container、login item 等の自動起動を解除する。
3. host-local の WORKFLOW / profile を rollback 用に保管するか、安全に削除する。
4. profile を停止してから `symphony-ready` の運用を止め、不要なラベルを任意で整理する。
5. GitHub / Codex の認証情報とトークンを provider 側で revoke し、host 上の複製を削除する。値そのものは記録しない。
6. 監査・復旧要件を確認してから workspace、cache、log を任意で削除する。
7. Issue、PR、commit、履歴は監査記録として原則保持する。

Excellent-Nd のアンインストールは Codex や GitHub 自体の削除を意味しません。

## トラブルシューティング

配信されない場合は、GitHub native state、adapter 接続、profile の `required_labels`、`symphony-ready`、Issueの `nd-target:<execution_target>`、repository台帳 `.excellent-nd/targets/`、host-local `host.json` のtarget ID一致を確認します。実行結果が不明な場合は、runtime log、Issue Workpad、Git 差分、検証、PR を順に確認します。Codex `workspace-write`では`.git`への書込みが意図的に保護されるため、`FETCH_HEAD`、branch、commit等の失敗をownership / permission変更や`danger-full-access`で迂回しません。clean workspaceはhost-side `before_run` hookで更新し、GitHubへのbranch / commit / PR作成はSymphonyのhost-side `github_api`を使用します。秘密情報を診断記録へ貼らないでください。
