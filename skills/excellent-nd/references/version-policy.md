# バージョン方針

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

## Excellent-Nd のバージョン番号

正式版は `X.Y`、beta / development版は `X.Y.Z`。`1.0.1` は `1.0` に向けた最初のcandidate。tagはHuman review後にmainへmergeされたcommitへ付ける。
