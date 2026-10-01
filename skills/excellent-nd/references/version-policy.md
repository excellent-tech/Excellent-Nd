# バージョン方針

現在のuser messageのcase-insensitiveな `@excellent-nd` は、ChatGPT自身の対応からExcellent-Nd → Issue → Symphony → Codexへの委譲を選ぶExecution Mode selectorであり、それ自体が人間の実行指示です。別個のHuman GO等は不要です。タグなしの自然言語、Skill自動選択、既存Issue、Plan metadataだけでは新しいdispatch / resumeを許可しません。

[Flow・continuation境界](../SKILL.md#明示的な実行指示)を参照してください。

version運用は2系統に分ける。

## 検証済み安定版

通常作業では、次の動作確認済みversion setを固定して使う。

- Symphony exact release / version
- Codex CLI / App Server exact version（固定可能な範囲）
- WORKFLOW / config revision
- Excellent-Nd Skill revision

exact versionと公式release assetのSHA-256は [`config/runtime-lock.json`](../../../config/runtime-lock.json) を正本とする。setup / smokeはこのmanifestを参照し、文書へ値を重複hard-codeしない。

より新しいstable releaseが存在しても、自動upgradeしない。

検証完了後にのみ新しいsetへ昇格する。

## 開発版

validated stableとは別に、新しいstable release、nightly、development versionを評価するprofileを持ってよい。

未検証のdevelopment profileを重要な実作業に使わない。

## 更新時の検証

任意upgradeでは、変更componentに応じた回帰テストを行う。

強制/必須upgradeでは、validated stableへ昇格する前に1.0.x全回帰テストを行う。

1. single Task end-to-end
2. multiple Task parallel execution
3. fixed execution-target routing
4. same-Task continuation
5. blocked → human decision → continuation
6. PR作成/更新とreview state
7. ChatGPTへのResult取り込み
8. Issue Task control / correlation metadata互換性
9. account usage / rate-limit handling
10. process restart / recovery

合格後に、実際に検証したexact version setをvalidated stableへ昇格する。可能なら旧validated setをrollback候補として保持する。

## Authorization / Flow回帰シナリオ

Skill更新時はfresh contextで次の判断を検証する。CLI testsは内部の `--explicit-mention` attestationと無指定・廃止flagの拒否を検証し、Chat messageの解釈はSkill behavioral testで確認する。CLI flag自体がChatのタグを検出するわけではない。

| Scenario | Expected behavior |
| --- | --- |
| 現在のmessageに `@ExCeLlEnT-Nd` と具体的Task、追加承認語なし | configured gates PASSならdispatch可能 |
| タグなしの「実行して」、Skill auto-selection | ChatGPT自身の対応まで。EN dispatch不可 |
| タグなしの「続けて」、Durable Issue / 過去Plan承認あり | 新しいdispatch / resumeのauthorizationではない |
| タグなしの「結果を取り込んで」、後続Taskの依存完了 | 結果を再統合。後続を自動routingしない |
| running Taskの同一Scope内でtest修正を継続 | Symphony / Codex thread continuation、新タグ不要 |
| Human Decision後、現在のmessageに `@excellent-nd` とresume指示 | 決定保存・configured gates確認後resume。追加Human GO不要 |
| Chat-created Issue、label / open gatesのみ | Chat direct-request + EN transportを維持、legacy Project gatesを追加しない |
| Draft PRあり、人間review / merge未実施 | AIによるmerge / Issue close / final completion不可 |

marker / observer / receipt / workspaceの既存unit testsも実行し、authorization修正がruntime lifecycleを巻き戻していないことを確認する。

## Excellent-Nd のバージョン番号

正式版は `X.Y`、beta / development版は `X.Y.Z`。`1.0.1` は `1.0` に向けた最初のcandidate。tagはHuman review後にmainへmergeされたcommitへ付ける。
