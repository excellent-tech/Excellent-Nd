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

Symphony実行制御の正本は、GitHub native state、adapterのdispatchability、profileで設定した `required_labels` を満たすrouting / execution-control labelである。標準routing labelは `symphony-ready`、可視化用は `nd-status:scheduled|running|blocked|review|failed`（原則1つ）とする。

通常Task用profileは明示的なexecution-control条件を要求する。bootstrap Issueにはその条件を付けず、Symphonyのdispatch対象にしない。runtime / profile検証完了後に作成する通常Taskからrouting条件を適用する。

| 情報 | 責務 |
| --- | --- |
| `workflow_status` | 人間向け表示、結果取り込み、論理的な進捗 |
| GitHub native state | active / terminalの判定 |
| `symphony-ready` | routing / 実行可否。status表示には使わない |
| `nd-status:*` | Issue一覧の可視化。実行制御には使わない |
| execution-target identity | routing先の識別。blocked中も変更しない |

running中にstatus表示目的で `symphony-ready` を外さない。Codex turn前failure等は自動更新主体がない場合があり、log / Workpad / Resultを根拠に人間またはChatGPTがfailed / blockedを更新する。customizeは `docs/operations.md` を参照する。

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
6. `workflow_status` を `scheduled` / 実行予定へ戻し、execution-control条件を再度有効化する。
7. 同じTask threadのcontinuationを優先する。

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
