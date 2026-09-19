# Single Task E2E 検証記録

この文書は、[Issue #4](https://github.com/excellent-tech/Excellent-Nd/issues/4) で実施した最初の通常 Task の検証項目を記録する。実行結果の正本は Issue Workpad と Pull Request とする。

## 検証経路

`GitHub Issue → Symphony → Codex → branch / change → verification → Pull Request / GitHub Result`

## チェックリスト

- bootstrap Task が完了し、runtime / profile の smoke verification が記録されている
- execution-control label の付与後に Symphony が通常 Task を取得している
- initial Codex turn に Issue body 由来の Execution Packet 全体が渡っている
- Task 専用の Codex thread と branch で documentation-only の変更を行っている
- 変更対象に適用可能な repository check と公開情報の確認を行っている
- commit、diff、verification、risk、remaining work を Issue Workpad に記録している
- review 可能な Pull Request を作成し、人間の review 前には merge していない

この検証は single Task の通常経路だけを対象とする。結果取り込み、continuation、並列 Task、Human Gate、複数 execution host は後続検証とする。
