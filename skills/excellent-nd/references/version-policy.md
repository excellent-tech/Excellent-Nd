# Version policy

version運用は2系統に分ける。

## Validated stable

通常作業では、次の動作確認済みversion setを固定して使う。

- Symphony exact release / version
- Codex CLI / App Server exact version（固定可能な範囲）
- WORKFLOW / config revision
- Excellent-Nd Skill revision

より新しいstable releaseが存在しても、自動upgradeしない。

検証完了後にのみ新しいsetへ昇格する。

## Development

validated stableとは別に、新しいstable release、nightly、development versionを評価するprofileを持ってよい。

未検証のdevelopment profileを重要な実作業に使わない。

## Upgrade validation

任意upgradeでは、変更componentに応じた回帰テストを行う。

強制/必須upgradeでは、validated stableへ昇格する前にV1全回帰テストを行う。

1. single Task end-to-end
2. multiple Task parallel execution
3. fixed execution-target routing
4. same-Task continuation
5. blocked → human decision → continuation
6. PR作成/更新とreview state
7. ChatGPTへのResult取り込み
8. Issue machine-readable schema互換性
9. account usage / rate-limit handling
10. process restart / recovery

合格後に、実際に検証したexact version setをvalidated stableへ昇格する。可能なら旧validated setをrollback候補として保持する。
