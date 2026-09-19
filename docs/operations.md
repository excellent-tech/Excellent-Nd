# 利用ガイド

[简体中文](operations.zh-CN.md) | [English](operations.en.md)

このガイドは、Excellent-Nd を導入・運用・停止する作業者向けの手順書です。バージョン番号の規則と現在の候補版は[バージョン方針](../skills/excellent-nd/references/version-policy.md)を参照してください。

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

### 3. GitHub を準備する

- **操作すること**: 対象リポジトリと認証を設定する。
- **コマンド / UI 操作**: GitHub App または公式連携へ、Issue・ラベル・ブランチ・PR に必要な最小権限を与える。秘密値はホストの秘密情報ストアへ保存する。
- **確認する結果**: テスト用 Issue の読み書きと、必要なブランチ・PR 操作が許可される。
- **OK の場合**: 手順 4 へ進む。
- **NG の場合**: GitHub 側のインストール先、権限、リポジトリ選択を修正する。秘密値を Issue やログへ貼らない。

### 4. Symphony と Codex を準備する

- **操作すること**: 実行ホストへ upstream の Symphony と Codex CLI / App Server を導入し、検証対象の正確なバージョンを固定する。
- **コマンド / UI 操作**: 各 upstream 文書に従ってインストールし、バージョン表示コマンドで実測値を記録する。
- **確認する結果**: Symphony と Codex App Server が起動でき、Git と GitHub に接続できる。
- **OK の場合**: 手順 5 へ進む。
- **NG の場合**: upstream の要件、実行権限、ネットワーク、認証を確認する。正常起動まで Issue を配信可能にしない。

> **挿図候補 2**: Symphony 起動後の正常状態を撮る。プロセスが稼働し、対象設定を読み込んだことだけが見えていればよい。トークン、非公開ホスト名、非公開パス、環境変数、内部 URL は写さない。

### 5. WORKFLOW、profile、GitHub Issues adapter を設定する

- **操作すること**: GitHub Issues adapter と対象ホスト用 profile を設定する。
- **コマンド / UI 操作**: initial prompt に `{{ issue.description }}` または同等値を含める。通常タスクの `required_labels` に `symphony-ready` を設定し、複数ホストでは条件が重複しないようにする。
- **確認する結果**: Issue body 全体が `issue.description` から Codex の最初の prompt へ渡り、対象外 Issue は配信されない。
- **OK の場合**: 手順 6 へ進む。
- **NG の場合**: WORKFLOW、profile、adapter の schema とラベル条件を修正し、Issue body が title だけへ縮退する構成を使用しない。

### 6. routing とステータスのラベルを作る

- **操作すること**: [ステータスラベル](#ステータスラベル)のラベルを作成する。
- **コマンド / UI 操作**: GitHub のラベル画面または記載の `gh label create` コマンドを使う。
- **確認する結果**: 実行承認済み Issue に `symphony-ready` と `nd-status:scheduled` を同時に付けられる。
- **OK の場合**: 手順 7 へ進む。
- **NG の場合**: ラベル名、権限、profile の `required_labels` を確認する。

> **挿図候補 3**: GitHub Issue に `symphony-ready` と `nd-status:scheduled` が付いた画面を撮る。2 種類のラベルが区別できればよい。Issue 本文中の秘密情報、非公開ホスト名、非公開 URL は写さない。

### 7. バージョン互換性と smoke verification を確認する

- **操作すること**: approval policy、sandbox、tool schema と構成全体を実測する。
- **コマンド / UI 操作**: adapter 接続、profile 読込、prompt、ラベル filter、App Server、Git / PR 権限、対象外 Issue の非配信を順に確認し、正確なバージョンと結果を Issue Workpad へ記録する。
- **確認する結果**: すべて成功し、秘密情報を含まない検証記録が残る。
- **OK の場合**: 手順 8 へ進む。
- **NG の場合**: 別バージョンの設定例を流用せず、固定したバージョンの schema を確認する。失敗中は通常タスクを配信しない。

### 8. 最初の single Task E2E を実施する

- **操作すること**: bootstrap とは別の通常タスクを、人間による実行承認（Human GO）後に実行する。
- **コマンド / UI 操作**: `ChatGPT → Issue → Symphony → Codex → branch / verification → PR → 人間レビュー` を通し、Workpad と PR へ結果を保存する。
- **確認する結果**: Issue body 全体が渡り、変更、検証、PR、レビュー待ち状態を追跡できる。
- **OK の場合**: 通常運用へ進む。
- **NG の場合**: runtime log、Workpad、Git 差分、検証、PR を確認し、原因を解消するまで追加タスクを配信しない。

Skill の導入だけでは実行環境の導入は完了しない。未導入ホストの bootstrap は、人間による実行承認（Human GO）と Issue 永続化の後に人間が明示的に開始する限定例外であり、通常タスクの手動実行経路ではない。

## 運用 / よくある質問

### Q. `@excellent-nd` はいつ付けますか？

A. 新しい会話、または Skill が自動選択されない場合に付けます。同じ会話で有効なら、毎回付ける必要はありません。

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

A. `owner` は成果の責任者、`execution_target` は Codex を動かす実行ホストの識別子です。実行先が未確定なら Issue を配信可能にしません。

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

## execution_target 方針

実行ホストの hostname を基本識別子とし、同一 LAN または組織の管理範囲で一意にします。Issue の存続期間中は変更せず、ホスト移行時は checkpoint を持つ後継 Issue を作ります。

公開リポジトリで非公開・内部 hostname がインフラ情報を漏らす場合は、`build-public-01` のような機密でない hostname または公開 alias を使い、対応表を公開物の外に保持します。既存 Issue の `execution_target` は書き換えません。

## ステータスラベル

| ラベル | 色 | 説明 |
| --- | --- | --- |
| `symphony-ready` | `0E8A16` | routing / 実行制御。ワークフロー状態ではない |
| `nd-status:scheduled` | `C2E0C6` | 人間による実行承認済み、実行待ち |
| `nd-status:running` | `1D76DB` | Codex が実行中 |
| `nd-status:blocked` | `D93F0B` | 人間判断、外部条件、利用枠を待機中 |
| `nd-status:review` | `FBCA04` | 人間レビュー待ち |
| `nd-status:failed` | `B60205` | 自動継続できない失敗。原因確認が必要 |

`nd-status:*` は原則 1 つだけ有効にします。running の表示だけを目的に `symphony-ready` を外しません。

作成例:

```sh
gh label create symphony-ready --color 0E8A16 --description "Routing / execution control"
gh label create "nd-status:scheduled" --color C2E0C6 --description "Human GO complete; waiting to run"
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

配信されない場合は、GitHub native state、adapter 接続、profile の `required_labels`、`symphony-ready`、実行先条件を確認します。実行結果が不明な場合は、runtime log、Issue Workpad、Git 差分、検証、PR を順に確認します。秘密情報を診断記録へ貼らないでください。
