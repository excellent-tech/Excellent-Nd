# execution_target / 実行ホスト台帳

## 原則

`execution_target` はTaskを実行するExcellent-Nd hostの安定IDである。Excellent-Ndは汎用品なので、実マシン数を固定値として持たない。登録数・有効数は対象repositoryの台帳から都度求める。

## Identity

- install時のlocal hostnameをtarget IDの既定値とする。
- target IDはinstall時に確定し、host-local `<prefix>/host.json` に固定する。
- runtime起動のたびにhostnameから既存IDを書き換えない。
- 1 Issueのlifetime中は変更しない。
- hostnameをGitへ載せたくない場合は `--execution-target build-01` のようなaliasを指定できる。
- explicit alias利用時、実hostnameは既定ではrepository台帳へ書かない。必要なら `--publish-hostname` を明示する。
- target IDはGitHub labelへ安全に写像できるよう、1-40文字の小文字英数字・dot・hyphenとする。

## Repository-local inventory

対象repository直下の次を台帳の正本とする。

```text
.excellent-nd/
├─ targets/
│  ├─ worker-a.json
│  ├─ worker-b.json
│  └─ ...
├─ host.json        # host-local / Git ignore
├─ WORKFLOW.md      # host-local / Git ignore
├─ symphony         # host-local / Git ignore
└─ workspaces/      # host-local / Git ignore
```

`targets/*.json` だけをGit管理し、それ以外のruntime stateはGit管理しない。1 host = 1 fileとし、複数hostによる更新競合を減らす。

例:

```json
{
  "schema": "excellent-nd/target@v1",
  "id": "worker-a",
  "hostname": "worker-a",
  "enabled": true,
  "routing_label": "nd-target:worker-a",
  "max_concurrent_agents": 1,
  "last_verified_at": "2026-09-24T00:00:00Z"
}
```

保存可能なのはroutingと実行能力判断に必要な非credential metadataだけとする。target ID、hostname、enabled、capacity、verification時刻は保存してよい。credential、token、password、private key、API key等の秘密値を保存しない。

setup/smokeがPASSした時点で自hostのrecordを作成・更新する。ChatGPT / Human / CodexはGitHub上の台帳を共通参照できる。作業マシンは自分のrecordを更新できるが、自動commit/pushはsetupの責務にしない。

登録台数は `targets/*.json` の件数、通常の割当候補数は `enabled: true` の件数として動的に集計する。静的台帳だけから現在onlineかどうかを推測しない。

## Routing

Task metadataの `execution_target: worker-a` はrouting label `nd-target:worker-a` へ1対1で写像する。

host-specific Symphony profileは次の両方を `required_labels` とする。

```yaml
required_labels:
  - symphony-ready
  - nd-target:worker-a
```

同一repositoryを複数hostが監視しても、自分のtarget labelを持つTaskだけをdispatchする。

`review` / `blocked` では `symphony-ready` を外して実行を停止する。target labelはcorrelation用に残してよい。

## Topology

### 1 repository -> N hosts

同じrepositoryに対してhostごとに別Symphony profile/processを起動し、各profileが異なる `nd-target:*` を要求する。台帳にはそのrepositoryで利用可能な0..N hostを登録する。

### N repositories -> 1 host

同一hostでrepositoryごとに別profile/processを起動する。各repositoryは自分の `.excellent-nd/targets/` に同じtarget IDを登録してよい。tracker repositoryとworkspaceはrepository単位で分離する。

## ChatGPTによるtarget選択

ChatGPTは固定的なマシン数や未確認hostを推測しない。

1. 対象repositoryの `.excellent-nd/targets/*.json` を確認する。
2. `enabled: true` のtargetを候補とする。
3. 候補が1台ならdefault targetとして提示できる。
4. 複数候補なら負荷・依存関係・利用者指示を基にPlanで割当を提示する。
5. 台帳が空、または利用可能targetがない場合はHumanへ確認し、target未確定Taskをdispatchableにしない。
