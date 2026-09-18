# Excellent-Nd 設計

本書は Excellent-Nd の設計判断の正本である。Symphony に関する事実は 2026-09-18 時点の OpenAI 公式リポジトリ `be10a1b79df723d6d7612b5651c8522704dafb2e` を確認した。未確定事項は [open-questions.md](open-questions.md) に分離する。

## 背景と課題

ChatGPT 上の相談は、要求整理、選択肢比較、Plan 作成、人間判断を一つの会話文脈で進めやすい。一方、小人数開発で人間がすべての作業を手作業で Issue 化・更新すると、管理自体が負担になりうる。

Excellent-Nd は、人間に Issue 管理を強いるのではなく、ChatGPT を主 UI としながら、実行時の Durable Task は GitHub Issue と Symphony に委ねる。

V1 では「Issue を使わない実行経路」を新たに作らない。人間から見た UX は Conversation-first、内部実行は Issue-first とすることで、独自 Runner や独自状態管理を増やさずに成立するかを検証する。

## 目的

Excellent-Nd は、ChatGPT 上の 1 つの Plan から 1 件以上の Task を切り出し、人間の GO 後に担当・依存関係・おおよその負荷配分を反映して GitHub Issue 化し、Symphony / Codex で実行する。

実行結果は GitHub に永続化し、人間が元の ChatGPT 会話で「結果を取り込んで」「状況を確認して」等と明示したときに、ChatGPT が各 Task の結果を取得して元 Plan へ再統合する。

## 設計原則

1. ChatGPT を要求整理、Plan、担当分割、GO、結果確認、次の判断の主 UI とする。
2. Human GO 前に実行しない。
3. 1 ChatGPT Chat は 1 つの計画・判断コンテキストとして扱い、そこから 1 件以上の Task に分岐できる。
4. 実行コンテキストは Task 単位とし、原則として 1 Task = 1 Codex thread とする。
5. 同じ Task の追加修正、test failure 修正、review 対応は同一 thread の継続を優先する。
6. V1 の実行 Task は GitHub Issue として Durable 化し、Symphony の Issue-first orchestration を利用する。
7. 全会話ではなく、Task ごとに必要な Execution Packet のみを実行側へ渡す。
8. Codex の生ログ全文ではなく、Git / test / diff 等の機械情報と短い要約からなる Execution Result を戻す。
9. GitHub 操作は ChatGPT の公式連携と Symphony の既存 integration を優先する。
10. Symphony と Codex が持つ scheduler / runner / workspace / retry / thread 管理を再実装しない。
11. ChatGPT への自動 push は V1 では行わず、人間の明示的な結果取り込みを基本とする。
12. 管理画面や状態を増やすより、人間が管理する情報量を減らす。

## V1 の全体モデル

```text
Human
  ↓
ChatGPT Chat
  - 要求整理
  - Plan
  - Task分割
  - 担当 / 負荷配分
  - Human GO
  ↓
GitHub Issues
  - Plan参照
  - Task参照
  - 担当
  - routing
  - Execution Packet
  ↓
Symphony
  ↓
Codex thread per Task
  ↓
Git / Test / PR / Issue Result
  ↓
GitHub
  ↓
Human: 「結果を取り込んで」
  ↓
ChatGPT
  - 複数TaskのResult取得
  - 元Planへ再統合
  - 次の判断
```

## Chat / Plan / Task / Codex thread の関係

### ChatGPT Chat

人間との計画・判断の文脈である。1 Chat 内で複数 Task を扱ってよい。

### Plan

Chat 内で合意した作業計画である。必要に応じ複数 Task に分割する。

V1 では Plan を独立 DB に保存しない。元 Chat と、GitHub Issue に記録する Plan 参照で相関できればよい。

### Task

Codex に渡す独立した実行目的である。

1 つの Plan から 1..N Task を生成できる。

例:

```text
Plan P-001
├─ T-001: 担当A
├─ T-002: 担当A
├─ T-003: 担当B
└─ T-004: 担当B
```

### Codex thread

Task を実行する AI 文脈である。

- 原則: 1 Task = 1 thread
- 同一 Task の継続: 同一 thread を優先
- 別 Task: 別 thread
- thread を再利用できない場合: Git + checkpoint から新規 thread で再開

Chat ID と Codex thread ID を 1:1 で固定しない。

## 複数 Task と担当配分

V1 では、ユーザーが 1 つの Plan 内で複数 Task の一括実行を指示できる。

例:

> Task 1〜10 を担当Aと担当Bに、おおよそ 3:7 の負荷で分けて進める。

ChatGPT は次を考慮して Task を割り当てる。

- 想定作業量
- Task 間の依存関係
- 並列実行可否
- ユーザーが指定した担当
- ユーザーが指定した概算負荷比率

3:7 等の比率は Task 件数の厳密比率ではなく、**おおよその総作業負荷**として解釈する。

V1 では高度な最適化 scheduler は作らない。ChatGPT が合理的な割当案を作り、人間が GO することで確定する。

## Human GO と一括 Issue 作成

Human GO 後、ChatGPT は実行対象 Task ごとに GitHub Issue を作成または更新する。

Issue には最低限、次を相関可能な形で記録する。

- Plan reference
- Task reference
- assignee / owner
- execution target / routing information
- objective
- constraints
- acceptance criteria
- relevant decisions
- relevant references
- dependencies

V1 では専用 DB を作らない。

## 実行 host と routing

V1 はまず 1 台の実行 host で end-to-end を検証し、安定後に同一 profile を 2 台目へ展開できる構成を目指す。

複数 host を使う場合、人間の責任者である `assignee` と、実際に Codex を動かす `execution target` を分離して扱う。

Symphony の `required_labels` 等、既存機能で Task を対象 host へ振り分けられる範囲を優先し、独自 scheduler は追加しない。

具体的な label 名や host routing 規則は PoC で確定する。

## Symphony の責務

[Symphony README](https://github.com/openai/symphony/blob/be10a1b79df723d6d7612b5651c8522704dafb2e/README.md)、[SPEC.md](https://github.com/openai/symphony/blob/be10a1b79df723d6d7612b5651c8522704dafb2e/SPEC.md)、[Elixir implementation README](https://github.com/openai/symphony/blob/be10a1b79df723d6d7612b5651c8522704dafb2e/elixir/README.md) から、V1 では次を Symphony に委ねる。

- Issue tracker polling
- dispatch / claim
- per-Issue workspace
- Codex App Server 起動
- thread / turn 管理
- continuation
- retry / backoff
- concurrency
- reconciliation
- runtime observability
- 取得可能な usage / rate-limit telemetry
- tracker integration

Excellent-Nd はこれらを複製しない。

## Codex App Server

Codex App Server は Symphony 固有機能ではなく、Codex を外部プログラムから制御するための公式インターフェースである。

Symphony は Codex App Server を利用して Task ごとの coding session を管理する。

Excellent-Nd は Codex App Server client を独自実装しない。

## Execution Packet

会話全文ではなく、Task ごとに最低限次を渡す。

| 項目 | 内容 |
| --- | --- |
| `plan_ref` | 元 Plan を識別する参照 |
| `task_ref` | Task を識別する参照 |
| `owner` | 人間側の担当 |
| `objective` | この Task で達成する目的 |
| `constraints` | 禁止事項、範囲、互換性、安全条件 |
| `acceptance_criteria` | 完了条件 |
| `relevant_decisions` | 実行に影響する確定済み判断 |
| `relevant_references` | Issue、文書、ファイル、commit 等 |
| `dependencies` | 先行 Task 等の依存関係 |

V1 では GitHub Issue body を最初の実体候補とし、専用 transport / DB を前提にしない。

## Execution Result

Codex / Symphony の結果は GitHub Issue / PR 等へ永続化し、ChatGPT は人間の明示的な取り込み指示時に取得する。

最低限次を扱う。

| 項目 | 内容 |
| --- | --- |
| `plan_ref` | 元 Plan の参照 |
| `task_ref` | Task の参照 |
| `status` | completed / blocked / failed 等 |
| `summary` | 人間判断用の短い要約 |
| `changed_files` | 変更ファイル |
| `diff_summary` | diff 統計・主要変更 |
| `verification` | test / check / exit status |
| `risks` | 既知リスク |
| `blockers` | 人間判断または外部条件待ち |
| `remaining_work` | 未完了範囲 |
| `references` | commit / PR / Issue 等 |

Git、test、diff、exit status 等の機械情報は、可能な限り元データを利用し、LLM に再生成させない。

## 結果の元 Chat への取り込み

V1 では自動 push を行わない。

人間が元 Chat で次のように指示する。

- 「結果を取り込んで」
- 「進行中 Task の状況を確認して」
- 「担当Aと担当Bの結果をまとめて」

ChatGPT は GitHub から Plan に紐づく各 Task / PR / verification を取得し、元 Plan の文脈へ再統合する。

この一操作で十分な間は、既存 Chat への自動書込み IF や独自 notification infrastructure を作らない。

## Human Gate

人間判断が必要になった Task は GitHub 上に blocked 状態と質問を残す。

例:

```text
Task → blocked
     → GitHubに質問・根拠を保存
     → 人間がChatGPTで状況取得
     → 人間が判断
     → ChatGPTが判断結果をGitHubへ反映
     → Task continuation
```

V1 では複雑な approval engine を作らない。

## checkpoint

Git は source、branch、commit、diff を保持する。

checkpoint は次を保持する。

- objective
- decisions
- completed work
- remaining work
- verification
- risks / blockers

Codex 会話全文を復旧の正本にしない。

## トークン削減

- Chat 全履歴を Task prompt にしない。
- Plan から各 Task に必要な情報だけ Execution Packet に切り出す。
- Task A の情報を Task B に不要なら渡さない。
- Codex の全イベント / ログを ChatGPT へ戻さない。
- Result は構造化し、人間の判断に必要な内容だけ ChatGPT で表示する。
- Git / test / diff / exit status 等は機械データを利用する。
- 同一 Task の continuation では thread 継続を優先する。

## V1 で扱わない領域

- Issue を使わない lightweight Task の直接実行経路
- lightweight / Durable Task の自動分類
- 自動 Task routing 最適化
- 担当者能力や過去実績に基づく自動配分
- リアルタイム負荷再配分
- quota / token 残量を使った自動 scheduling
- ChatGPT への自動 push / 既存 Chat への外部書込み
- 独自 notification daemon / webhook relay
- Symphony fork / 再実装
- 独自 Codex Runner / Codex App Server client
- 独自 scheduler / retry / workspace manager
- 独自 DB / SQLite
- 独自 GitHub API client
- 独自 Kanban / 大型 Web UI
- multi-agent orchestration
- 複数 AI provider
- 複数 tracker
- SaaS / multi-tenant
- 汎用 workflow engine

将来候補は実運用で不足が確認された場合のみ再検討する。
