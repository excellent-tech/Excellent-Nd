# execution_target / 実行ホスト台帳

## Identity

`execution_target` はTaskを実行するExcellent-Nd hostの安定IDである。

- 非公開repositoryでは、install時のlocal hostnameを既定値としてよい。
- 値はinstall時に確定し、host-local `<prefix>/host.json` へ保存する。
- runtime起動のたびにhostnameを再読込して既存IDを書き換えない。
- 1 Issueのlifetime中は変更しない。
- public repositoryで実hostnameがinfra情報を漏らす場合は、`--execution-target build-public-01` のようなnon-sensitive aliasを使う。
- target IDはGitHub labelへ安全に写像できるよう、1-40文字の小文字英数字・dot・hyphenとする。

## Routing

Task metadataの `execution_target: worker-a` は routing label `nd-target:worker-a` へ1対1で写像する。

host-specific Symphony profileは次の両方を `required_labels` とする。

```yaml
required_labels:
  - symphony-ready
  - nd-target:worker-a
```

これにより同一repositoryを複数hostが監視しても、自分のtarget labelを持つTaskだけをdispatchする。

`review` / `blocked` では `symphony-ready` を外して実行を停止する。target labelはcorrelation用に残してよい。

## Topology

### 1 repository -> N hosts

同じrepositoryに対してhostごとに別Symphony profile/processを起動し、各profileが異なる `nd-target:*` を要求する。

### N repositories -> 1 host

同一hostでrepositoryごとに別profile/processを起動する。各profileは同じexecution target IDを使ってよいが、tracker repositoryとworkspace rootはrepository単位で分離する。

## Host-local record

各runtime prefixの `host.json` が「このprofileがどのtargetとして動くか」の正本である。

```json
{
  "schema": "excellent-nd/host@v1",
  "repository": "owner/repository",
  "execution_target": "worker-a",
  "routing_label": "nd-target:worker-a"
}
```

これはhost-local fileであり、通常はGit管理しない。

## Central inventory / 台帳

組織内で「どの作業マシンがあるか」「何台登録されているか」「どのrepositoryを担当するか」を把握する場合、独自DBや新サービスではなく、**organization管理のprivate Git repository**を台帳の正本とすることを推奨する。

```yaml
schema: excellent-nd/targets@v1
targets:
  - id: worker-a
    hostname: internal-host-a
    enabled: true
    repositories:
      - owner/repo-a
      - owner/repo-b
    max_concurrent_agents: 1
    last_verified_at: "2026-09-24T00:00:00Z"
```

- `id`: Issue / routingに使うtarget ID。public repoへ出る可能性がある場合はpublic-safe alias。
- `hostname`: 実hostname。private inventoryだけに保持してよい。
- `enabled`: 新規Taskの割当候補か。
- `repositories`: そのhostでprofileが構成済みのrepository。
- `max_concurrent_agents`: capacityの参考値。scheduler機能ではない。
- `last_verified_at`: 最後にsetup/smokeを確認した時刻。

credential、token、秘密鍵は台帳へ保存しない。

登録台数は `targets` の件数、通常の割当可能台数は `enabled: true` の件数として機械的に集計できる。online状態をこの静的台帳だけから推測しない。

## ChatGPTによるtarget選択

ChatGPTはtargetを推測しない。

1. private target inventoryまたは現在のPlanで利用可能targetを確認する。
2. repository assignmentとenabled状態を確認する。
3. 候補が1台ならdefault targetとして提示できる。
4. 複数候補なら負荷・依存関係・利用者指示を基にPlanで割当を提示する。
5. inventoryが取得できない場合はHumanへ確認し、target未確定のTaskをdispatchableにしない。
