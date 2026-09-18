# 未確定事項

ここには V1 着手前または初期検証で判断が必要な事項だけを記載する。候補は確定仕様ではない。

| 未確定事項 | 確認すること | 判断結果が影響する範囲 |
| --- | --- | --- |
| ChatGPT から Codex 実行開始までの最小経路 | 利用可能な公式連携、認証境界、同期 / 非同期の制約 | V1 の入口と transport |
| lightweight Task の実行方法 | Issue なしで Codex を開始・観測・停止する最小手段 | Symphony を使わない経路の要否 |
| Symphony と直接 Codex 実行の使い分け | 作業時間、共有、再開、Human Gate、履歴の観点での境界 | lightweight / Durable Task の運用基準 |
| ChatGPT への結果返却方法 | pull で status / result を取得できるか、参照先をどう示すか | V1 の出口 |
| Human Gate の再開方法 | blocked / question の表現、回答の渡し方、同一 thread 継続可否 | continuation と checkpoint |
| token / usage 情報 | Codex App Server と Symphony が安定して提供する項目、集計単位、欠損時の扱い | Execution Result と可観測性 |
| GitHub Issue への昇格条件 | 手動判断に必要な最小チェック項目、実行途中の昇格方法 | Durable Task 作成 |
| ChatGPT Skill の責務 | Plan の圧縮、Packet 作成、GO 確認、Result 表示のどこまでを担うか | ChatGPT 側の最小構成 |
| Symphony reference implementation の利用形態 | 評価用 Elixir 実装をそのまま使う範囲、設定 / profile だけを提供する案、安全要件 | 配布・運用・保守 |
| upstream Symphony 追従 | Draft 仕様と prototype の変更検知、互換性確認、固定する version / commit | 継続保守 |
| Execution Packet / Result の表現 | Markdown、JSON 等の候補と、schema を固定する最小時期 | 受渡しと検証 |
| checkpoint の保存先 | GitHub Issue、repository 内 artifact、その他既存機能のどれで十分か | 別 thread / 別マシン再開 |
