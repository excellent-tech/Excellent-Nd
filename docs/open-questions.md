# 未確定事項

V1 の基本構成は次で固定する。

> ChatGPT → Plan / Task分割 / Human GO → GitHub Issues → Symphony → Codex → GitHub Result → 人間の明示的な取り込み → ChatGPT

## 確定した設計判断

- 1 Issue = 1 execution target とし、Issue lifetime 中は host を固定する。
- host 移行は同じ Issue の書換えではなく、checkpoint を持つ後継 Issue を作成する。
- active workflow state は 実行予定 / 処理中 / 保留 / レビュー とする。
- blocked は人間回答後に同じ Task を continuation する。
- 同一 Task は原則同一 Codex thread を再利用する。明示分割、context 限界、resume 不能、host 移行時は新 thread へ引き継ぐ。
- Issue body 全体をExecution Packetとし、人間向けMarkdown + Task control / correlation metadata JSON blockとする。
- Symphony未導入hostのbootstrapはHuman GOとIssue記録を必須とし、通常routing条件を付けない限定例外とする。runtime / profileのsmoke verification後、別の通常Taskでsingle Task E2Eを行う。
- checkpoint は Issue Workpad + branch / commit + PR を基本とする。
- 数時間・週次 usage limit は短周期 retry 対象にせず、reset 後の安全な既存再開手段または人間の再開指示を利用する。
- ChatGPT 共通 workflow は `skills/excellent-nd/` で管理する。
- version は validated stable / development を分離し、stable は latest へ自動追従しない。強制更新は V1 全回帰テストを必須とする。

## PoC で残る未確定事項

| 未確定事項 | 確認すること | 判断結果が影響する範囲 |
| --- | --- | --- |
| GitHub credential | GitHub adapter / provider-native tool が Issue、comment、branch、PR に必要とする実測最小権限 | セキュリティ |
| multi-host routing | required labels の組合せだけで複数 Symphony instance の重複取得を確実に避けられるか | 複数 host 運用 |
| worker境界を越えた thread continuation | worker終了・process restart 後も同一 Task thread をどこまで resume できるか | context / token 効率 |
| long-window usage-limit resume | rate-limit reset timestamp を利用して、独自 scheduler なしで安全に数時間〜週次枠後の自動再開ができるか | 自動再開 |
| Human Gate 実装 | control label を外す / 戻す運用で running agent の停止と continuation が安定するか | 保留 / 再開 |
| Result workpad format | Issue Workpad / PR body の最小定型で人とAI双方が十分に状態把握できるか | 結果取り込み |
| version compatibility | Symphony / Codex / WORKFLOW / Skill の組合せをどこまで version set として固定する必要があるか | 保守 |

## V1 外として保留する事項

- 通常TaskでIssueを使わない lightweight Task の直接実行経路
- ChatGPT への自動 push / 既存 Chat への直接書込み
- 独自 notification daemon / webhook relay
- 自動負荷最適化 / 自動再配分
- 独自 quota-aware scheduler
- 独自 Runner / DB / scheduler
- Symphony fork
- multi-agent / multi-provider / multi-tenant
