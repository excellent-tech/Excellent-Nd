# execution_target と作業マシン台帳

この文書は、1つのrepositoryに0..N台のExcellent-Nd作業マシンを登録し、追加・無効化・削除する運用を定義する。

## 1. 登録されるタイミング

作業マシンの登録はsetup開始時ではない。次の2段階で成立する。

1. **ローカル登録候補の生成**  
   `scripts/setup.py` が前提条件、GitHub認証、Symphony checksum、Codex互換性、WORKFLOW生成、routing label準備を行い、smoke verificationがPASSした後に `.excellent-nd/targets/<target-id>.json` を生成・更新する。smokeが失敗した場合は共有台帳へ登録しない。
2. **共有台帳への正式登録**  
   生成されたtarget fileをreviewし、Git commit / pushし、運用ブランチ（通常はmain）へ反映する。この時点からChatGPT / Human / 他の作業マシンがGitHub経由で同じ登録情報を参照できる。

setupはtarget fileを自動commit / pushしない。登録内容を人間が確認できるようにするためである。

`enabled: true` は「このrepositoryの実行先として割当可能」という管理状態であり、現在processがonlineであることを示すheartbeatではない。

## 2. 最初の作業マシンを登録する

repository rootで実行する。

```bash
python3 scripts/setup.py \
  --repo OWNER/REPOSITORY \
  --repo-path . \
  --prefix .excellent-nd \
  --skill-confirmed
```

target IDの既定値はlocal hostnameである。hostnameをGitへ載せたくない場合はaliasを明示する。

```bash
python3 scripts/setup.py \
  --repo OWNER/REPOSITORY \
  --repo-path . \
  --prefix .excellent-nd \
  --execution-target worker-a \
  --skill-confirmed
```

smoke PASS後:

```text
.excellent-nd/
└─ targets/
   └─ worker-a.json
```

内容を確認し、秘密情報がないことを確認してcommitする。

```bash
git add .excellent-nd/targets/worker-a.json
git commit -m "ops: register Excellent-Nd target worker-a"
git push
```

branch protectionを使うrepositoryではPRを作り、merge後に共有登録成立とする。

## 3. 2台目以降を登録する

各作業マシンで同じsetupを実行する。1 host = 1 fileなので、複数hostが同時に登録しても同じ台帳ファイルを編集しにくい。

```text
.excellent-nd/targets/
├─ worker-a.json
├─ worker-b.json
└─ worker-c.json
```

各host-specific Symphony profileは次を要求する。

```yaml
required_labels:
  - symphony-ready
  - nd-target:<this-host-target-id>
```

Issueの `execution_target` と `nd-target:<id>` が一致するhostだけがTaskを取得する。

登録数は固定値を持たず、`.excellent-nd/targets/*.json` の件数から求める。通常の割当候補は `enabled: true` のrecordだけとする。

```bash
python3 scripts/target_inventory.py list --repo-root .
```

## 4. 作業マシンを一時的に無効化する

一時停止、保守、長期停止では、いきなり台帳fileを削除しない。

1. 対象recordの `enabled` を `false` に変更する。
2. commit / push / mergeして、ChatGPTが新規Taskの候補に選ばない状態にする。
3. 対象targetのopen Issueを確認する。
4. 実行中Taskは完了させるか、停止して後継Issueへcheckpointを引き継ぐ。
5. 必要に応じてSymphony profile/runtimeを停止する。

```json
{
  "schema": "excellent-nd/target@v1",
  "id": "worker-b",
  "hostname": "worker-b",
  "enabled": false,
  "routing_label": "nd-target:worker-b",
  "max_concurrent_agents": 1,
  "last_verified_at": "2026-09-25T00:00:00Z"
}
```

既存Issueの `execution_target` は書き換えない。別hostへ移す場合はcheckpointを保存した後継Issueを作成する。

## 5. 作業マシンを削除する

削除は **disable → drain → delete** の3段階とする。

1. `enabled: false` を共有台帳へ反映する。
2. そのtargetを参照するactive Taskがないことを確認する。残っている場合は完了、blocked、または後継Issueへの移行を行う。
3. 対象hostのSymphony/runtimeを停止する。
4. target recordを削除する。

```bash
git rm .excellent-nd/targets/worker-b.json
git commit -m "ops: remove Excellent-Nd target worker-b"
git push
```

5. branch protectionがある場合はPRをmergeする。
6. host-localの `.excellent-nd/host.json`、WORKFLOW、workspace、runtimeは、監査・rollback要件を確認してから任意で削除する。

`nd-target:<id>` GitHub labelは、過去Issueのrouting履歴を読みやすく保つため**既定では削除しない**。完全cleanupが必要な場合だけ、過去Issueへの影響を確認して別途削除する。

## 6. 再登録

同じtarget IDを再利用できる状態なら、そのhostでsetupを再実行する。smoke PASS後にrecordが再生成・更新されるため、reviewしてcommit / mergeする。

hostname変更等でtarget identity自体が変わる場合は、旧targetをrenameしない。新targetを登録し、旧targetをdisableし、既存Taskをcheckpoint付き後継Issueへ移行した後に旧recordを削除する。

## 7. 保存可能なデータ

台帳はroutingと実行能力判断に必要な非credential metadataだけを保持する。

| データ | 保存 |
| --- | --- |
| target ID | 可 |
| hostname | 可 |
| enabled | 可 |
| max_concurrent_agents | 可 |
| last_verified_at | 可 |
| routing label | 可 |
| token / password / API key | 禁止 |
| private key / credential | 禁止 |

hostnameは通常の内部名称として保存できる。名称自体に公開したくない情報が含まれる環境ではaliasを使う。

## 8. ChatGPTの割当規則

ChatGPTは固定的なマシン台数を仮定しない。

1. target repositoryの `.excellent-nd/targets/*.json` を読む。
2. `enabled: true` のrecordだけを新規Task候補とする。
3. 候補が1台ならdefault candidateにできる。
4. 複数台なら負荷、依存関係、利用者指示を基にPlanで割当する。
5. 候補が0台ならtarget未確定のままdispatchableにしない。
