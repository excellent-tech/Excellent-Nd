# V1 スコープ

## V1 の目的

V1 は、次の 1 本の経路が現在の開発環境で成立することを確認する。

> ChatGPT で Plan を作成 → Human GO → 1 Task を Codex へ渡す → 実行 → 構造化結果を ChatGPT から確認する

新しい管理基盤を作ることではなく、会話と実行環境を最小限の情報で安全につなぐことが目的である。

## V1 対象

- ChatGPT を要求整理、Plan、GO、結果確認、blocked 確認、次の判断の主 UI とする。
- Human GO 後に Plan から 1 Task を切り出す。
- objective、constraints、acceptance criteria、relevant decisions、relevant references を含む Execution Packet を作る。
- Codex が利用できる Git 管理下の対象開発環境へ Task を渡す。
- Durable Task では GitHub Issue と Symphony の Issue-first execution を利用する。
- lightweight Task は Issue を必須にしない。ただし実行経路は事前検証で決める。
- status、summary、changed files、diff summary、verification、risks、blockers、remaining work を含む Execution Result を返す。
- Git / test / diff / exit status と、取得可能な usage 情報を機械的に構造化する。
- 同じ Task の継続と Human Gate 後の再開を検証する。
- Git 状態と checkpoint から別 thread / 別マシンで再開できる最小条件を確認する。
- GitHub 操作は公式連携または Symphony の既存 integration を優先する。

## V1 非対象

- Symphony の再実装または fork の改変
- 独自 Codex Runner、独自 agent harness
- 独自 scheduler、retry、concurrency、workspace manager
- lightweight / Durable Task の自動判定や高度な routing
- multi-agent orchestration、複数 AI provider
- SaaS、multi-tenant、大規模チーム向け scheduler
- Backlog / Jira 等を含む複数 tracker 対応
- 独自 Kanban、大型 Web UI、独自 Project 管理
- 大規模な中央 DB、独自 SQLite を前提とする状態管理
- 複雑な approval engine
- 独自 notification daemon、webhook relay、ChatGPT への独自 push 通知
- 汎用 workflow engine

## 成功条件

1. ChatGPT 上の Plan から、人間が GO を出した 1 Task だけを実行できる。
2. 会話履歴全文を渡さず、Execution Packet で Codex が必要な作業を完了できる。
3. 実行後、ChatGPT から Execution Result を確認し、次の判断ができる。
4. Git / test / diff / exit status を、LLM の推測ではなく取得元の事実として確認できる。
5. blocked 時に Human Gate へ戻り、判断後に同じ Task を継続できる。
6. Durable Task は GitHub Issue と Symphony を使って実行できる。
7. Issue を作らない lightweight Task の最小経路について、採用可否を判断できる検証結果がある。
8. 独自 Runner、独自 DB、独自 scheduler、Web UI、通知基盤を作らずに上記を満たす。

## 実装開始前の検証事項

優先順に検証する。

1. ChatGPT から Codex 実行開始までの最小経路と、利用可能な公式連携の境界。
2. Symphony の GitHub Issues adapter を使う Durable Task の end-to-end 経路。
3. Issue を作らない lightweight Task を Symphony なしで直接実行するか、別の最小経路を使うか。
4. Execution Packet の最小形式と、Codex に渡る情報の確認方法。
5. Execution Result を ChatGPT から取得する方法と、機械情報・LLM 要約の分離。
6. 同一 Task の thread 継続、Human Gate 後の再開、checkpoint からの再開。
7. Symphony / Codex から取得できる token、usage、rate-limit 情報の範囲と安定性。
8. 公式 Elixir reference implementation を利用できる範囲、安全要件、upstream 追従方法。

検証結果が出るまで、transport、保存形式、軽量 Task の実行方式、reference implementation の採否を確定仕様にしない。
