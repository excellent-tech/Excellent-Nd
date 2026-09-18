# Workflow conventions

## 人間向け状態

V1では次の4つのactive workflow stateを使う。

| 表示 | Machine value | 意味 |
| --- | --- | --- |
| 実行予定 | `scheduled` | Human GO済みで実行可能 |
| 処理中 | `running` | Codexが処理中 |
| 保留 | `blocked` | 人間判断、外部条件、利用枠等で停止 |
| レビュー | `review` | 実装・検証が終わりレビュー待ち |

表示状態とexecution control labelを分離する。profile側ではexecute/ready labelとexecution target別routing labelを使ってよい。

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
2. stateを `blocked` / 保留にする。
3. Symphonyがcontinuationしないようexecution-control条件を外す。
4. execution-target routing identityは変更しない。
5. 人間回答後、stateを `scheduled` / 実行予定へ戻し、executionを再度有効化する。
6. 同じTask threadのcontinuationを優先する。

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

V1では独自quota-aware schedulerを作らない。手動再開または既存schedulerが実運用上の負担になった場合のみ再検討する。
