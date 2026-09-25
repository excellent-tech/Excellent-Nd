# Workflow conventions

## 人間向け状態

1.0.xでは次の4つのactive workflow stateを使う。

| 表示 | Machine value | 意味 |
| --- | --- | --- |
| 実行予定 | `scheduled` | 人間による実行承認（Human GO）済みで実行可能 |
| 処理中 | `running` | Codexが処理中 |
| 保留 | `blocked` | 人間判断、外部条件、利用枠等で停止 |
| レビュー | `review` | 実装・検証が終わりレビュー待ち |

`workflow_status` はExcellent-Ndと人間向けの論理状態であり、それ自体はSymphonyをdispatch / stopさせない。

Symphony実行制御の正本は、GitHub native state、adapterのdispatchability、profileで設定した `required_labels` を満たすrouting / execution-control labelである。通常Taskでは対象repositoryの `.excellent-nd/repository.json` で定義されたrouting labelとhost-specific target labelを要求する。可視化用status labelsもrepository configのmappingを正本とする。標準値は configured routing label / `nd-target:*` / `nd-status:*` だが、固定値として扱わない。

## 明示的dispatch gate

通常Taskは、現在のuser messageのcase-insensitiveな `@excellent-nd` と、同じmessageまたは同一決定文脈の人間による実行承認（Human GO）の両方を要求する。Skillの自動選択はgateを満たさない。片方でも欠ければChatGPT内のPlan・調査・安全なGitHub操作までとし、routing labelを追加・復元しない。

`review` / `blocked`への遷移は、状態更新と同じIssue updateでrepository configのrouting labelを外す。再開時は両gateを再確認し、reasonをWorkpadへ保存してからscheduledとroutingを復元する。

通常Task用profileはrepository configのrouting labelとhost-specific target labelの両方をexecution-control条件として要求する。bootstrap Issueにはその条件を付けず、Symphonyのdispatch対象にしない。runtime / profile検証完了後に作成する通常Taskからrouting条件を適用する。target候補は対象repositoryの `.excellent-nd/targets/*.json` を参照し、固定的な台数を仮定しない。

| 情報 | 責務 |
| --- | --- |
| `workflow_status` | 人間向け表示、結果取り込み、論理的な進捗 |
| GitHub native state | active / terminalの判定 |
| configured routing label | routing / 実行可否。status表示には使わない |
| configured status labels | Issue一覧の可視化。実行制御には使わない |
| execution-target identity | routing先の識別。blocked中も変更しない |

running中にstatus表示目的で configured routing label を外さない。Codex turn前failure等は自動更新主体がない場合があり、log / Workpad / Resultを根拠に人間またはChatGPTがfailed / blockedを更新する。customizeは `docs/operations.md` を参照する。

## Continuation

同じTaskでは、利用可能なら同一Codex threadを優先する。

新しいthreadへ切り替える条件:

- ユーザーが明示的にthread分割を指示した
- contextが大きすぎる、または信頼できなくなった
- threadをresumeできない
- 新しいexecution targetへ移行し、後継Issueになった
- Task目的が実質的に別Taskへ変わった

引継ぎにはGit状態とIssue checkpointを使い、過去chat全文を必須にしない。

## 保留と再開

人間判断でblockedになった場合:

1. Issue Workpadへ理由と具体的質問を保存する。
2. `workflow_status` を `blocked` / 保留にする。
3. Symphonyがdispatch / continuationしないようexecution-control条件を外す。
4. execution-target routing identityは変更しない。
5. 人間回答をIssueへ保存する。
6. 現在のuser messageで `@excellent-nd` と人間による実行承認（Human GO）を再確認し、resume reasonをWorkpadへ保存する。
7. `workflow_status` を `scheduled` / 実行予定へ戻し、execution-control条件を再度有効化する。
8. 同じTask threadのcontinuationを優先する。

## Runtime interruption record

同一process treeのobserverはstructured log / observable eventを受け、Issue contextを持つnon-transient interruptionだけをsanitized Workpadへ記録する。取得不能な値は推測せず、transient retryはSymphonyへ委ねる。observerはscheduler、retry queue、workspace managerを持たず、Symphony起動、event観測、Excellent-Nd固有のGitHub同期だけを行う。

## Account usage / rate-limit exhaustion

数時間または週次のaccount usage limitに対して、短周期のtransient retryを主手段にしない。

信頼できるreset timestampが取得できる場合:

- usage-limit理由とreset timestampをIssue Workpadへ保存する。
- Taskを `blocked` / 保留にする。
- 既存の対応済みschedulerがある場合に限り、reset時刻以降に再開する。

信頼できるreset timestampまたは安全なschedulerがない場合:

- usage-limit状態を保存する。
- Taskを保留したままにする。
- 人間が後から明示的に再開する。

1.0.xでは独自quota-aware schedulerを作らない。手動再開または既存schedulerが実運用上の負担になった場合のみ再検討する。
