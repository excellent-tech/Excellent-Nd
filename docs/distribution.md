# 配布とPublic Plugin準備

Excellent-Ndの主配布経路は、ChatGPT / Codexが共有するPublic Plugin Directoryを想定する。GitHub Releaseはfallback / source distributionとして維持する。

正式申請は、別のclean machineでPlugin install、execution-host setup、single Task E2E、interruption/status handlingを確認し、人間による申請承認を得た後に行う。

## Portable Plugin

repository rootをportable plugin rootとして扱う。

- `plugin.json`: Agent Plugins 1.0のportable manifest
- `skills/excellent-nd/`: ChatGPT / Codexで利用するSkill
- `scripts/`: execution-host bootstrap / smoke / runtime observer
- `config/`: WORKFLOW template / validated runtime lock
- `LICENSE`, `THIRD_PARTY_NOTICES.md`: license / attribution

この段階ではSkill-only Pluginとして扱い、`mcp.json`、`.mcp.json`、`.app.json`は同梱しない。独自Remote MCPは追加しない。

## Package build

```bash
python3 scripts/build_plugin_package.py --check-only
python3 scripts/build_plugin_package.py --output dist/excellent-nd-plugin.zip
```

生成物:

- `dist/excellent-nd-plugin.zip`
- `dist/excellent-nd-plugin.zip.sha256`

ZIPのrootには `plugin.json` が置かれる。buildはfile orderとZIP timestampを固定し、同じsourceから再現可能なpackageを生成する。

## Repository marketplace

`.agents/plugins/marketplace.json` はrepository rootのportable pluginをlocal sourceとして公開する。

Git repositoryをmarketplace sourceとして登録する場合:

```bash
codex plugin marketplace add excellent-tech/Excellent-Nd --ref <branch-or-tag>
```

開発中はpackage preparation branch / commitをpinし、別マシン検証時に同じrevisionを使用する。Public Plugin申請前にmainへmergeし、検証済みrevisionを固定する。

## 別マシン検証Gate

正式申請前に次を別のclean execution machineで確認する。

1. marketplaceからExcellent-Ndを発見・installできる。
2. `excellent-nd` Skillを新規Chatで利用できる。
3. `@excellent-nd`なしではCodex dispatchされない。
4. Codexへexecution-host setupを依頼し、Symphony / Codex / GitHub / WORKFLOW / observer / smokeを準備できる。
5. 小さいsingle Task E2Eが `ChatGPT -> Issue -> Symphony -> Codex -> PR -> review` まで到達する。
6. simulated interruptionでWorkpad、blocked、routing停止、secret redactionを確認する。
7. review待ちで `symphony-ready` が残らず再dispatchされない。

別マシン検証がPASSするまではPublic Plugin提出を行わない。

## GitHub Release fallback

Public Plugin Directoryを利用できない環境向けに、GitHub Releaseには次を置く。

- portable Plugin ZIP
- SHA-256
- source archive
- release notes
- manual / advanced installation guide

Public PluginとGitHub Releaseは同じsource revisionから生成し、内容差を作らない。


## execution_target routing prerequisite

1 repositoryを複数execution hostで安全に処理するには、各hostのprofileが `symphony-ready` と固有の `nd-target:<execution_target>` を両方要求する。install時target IDはlocal hostnameを既定値にする。hostnameをrepositoryへ載せたくない場合は明示aliasを使える。対象repositoryの `.excellent-nd/targets/*.json` をGit管理し、登録hostをChatGPT / Human / Codexが共通参照する。台帳にcredentialやsecretは保存しない。

別マシン検証では、同一repositoryを2 profileで監視してもtarget不一致のhostがTaskを取得しないnegative testを含める。


## 3-level installation

Public distribution must explain three independent installation levels:

1. ChatGPT Skill
2. Repository / Issue integration
3. Execution host runtime

Level 2 is Chat-first. The target repository is audited for existing labels, Issue templates/forms, and automation before `.excellent-nd/repository.json` is created. Execution-host setup fails closed without an approved repository config. Existing labels are never overwritten by setup.
