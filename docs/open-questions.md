# 未確定事項

V1 の基本構成は次で固定する。

> ChatGPT → Plan / Task分割 / Human GO → GitHub Issues → Symphony → Codex → GitHub Result → 人間の明示的な取り込み → ChatGPT

以下だけを PoC で確定する。

| 未確定事項 | 確認すること | 判断結果が影響する範囲 |
| --- | --- | --- |
| execution host routing | 2台以上へ展開した際に、Symphony の required labels 等だけで重複実行なく担当 host を固定できるか | 複数 host 運用 |
| routing label / state 規則 | GO、running、blocked、review、再開を最小の label / Issue state でどう表現するか | GitHub 運用 |
| GitHub credential | Symphony GitHub adapter / provider-native tool に必要な最小権限 | セキュリティ |
| Human Gate 再開 | blocked 時に routing を停止し、人間回答後に安全に continuation できるか | continuation |
| thread 継続 | 同一 Task の continuation で thread をどこまで再利用できるか | token / context 効率 |
| Execution Packet の具体形式 | Issue body の Markdown で十分か、machine-readable block が必要か | Task受渡し |
| Execution Result の具体形式 | Issue comment / PR body のどこまでを定型化するか | 結果取り込み |
| checkpoint 保存形式 | Issue comment、PR、repository artifact のどれが最小か | 再開・引継ぎ |
| usage telemetry | Codex App Server / Symphony が安定して提供する token / rate-limit 項目 | 可観測性 |
| ChatGPT Skill の必要性 | Plan分割、GO、Issue一括作成、Result取り込みをSkill化すると十分な再現性が得られるか | ChatGPT側UX |
| upstream Symphony 追従 | stable releaseをどの単位で固定し、更新時に何を再検証するか | 保守 |

## V1 外として保留する事項

以下は未確定ではなく、V1 では実装しない。

- Issue を使わない lightweight Task の直接実行経路
- ChatGPT への自動 push / 既存 Chat への直接書込み
- 独自 notification daemon / webhook relay
- 自動負荷最適化 / 自動再配分
- quota-aware scheduling
- 独自 Runner / DB / scheduler
- Symphony fork
- multi-agent / multi-provider / multi-tenant
