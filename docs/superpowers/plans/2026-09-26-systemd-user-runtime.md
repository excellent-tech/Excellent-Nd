# systemd user runtime implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Linux runtime を repository 単位の systemd user service として安全に常駐させる。

**Architecture:** 共有 unit template と instance mapping を追加し、薄い entrypoint が `gh auth token` を process environment にだけ渡して既存 observer を起動する。setup は systemd lifecycle と process tree を検証する。

**Tech Stack:** Python standard library, systemd user services, unittest

**Spec:** `docs/superpowers/specs/2026-09-26-systemd-user-runtime-design.md`

## Global Constraints

- credential と private repository 固有値を public artifact または unit/mapping の credential field に保存しない。
- 既存 observer/Symphony orchestration を再実装しない。
- Linux 以外の `--start` は fail-closed、診断用途は `--foreground` を使う。

---

### Task 1: service configuration contract

**Files:** `scripts/systemd_service.py`, `config/excellent-nd@.service.tpl`, `tests/test_systemd_service.py`

- [x] instance validation、mapping collision、unit rendering、secret 非混入の failing tests を追加して失敗を確認する。
- [x] standard library のみで最小実装し、対象 test を通す。

### Task 2: credential-safe service entrypoint

**Files:** `scripts/service_runner.py`, `tests/test_service_runner.py`

- [x] mapping/path 検証と `gh auth token` の一時 environment 注入を表す failing tests を追加して失敗を確認する。
- [x] observer への `execve` だけを実装し、対象 test を通す。

### Task 3: setup lifecycle

**Files:** `scripts/setup.py`, `tests/test_setup.py`

- [x] `--start`、`--foreground`、unsupported environment、active/process validation の failing tests を追加して失敗を確認する。
- [x] Linux systemd user lifecycle を接続し、setup/smoke regression tests を通す。

### Task 4: operations and host verification

**Files:** `docs/operations.md`

- [x] service/status/log/process の匿名化された運用手順を追加する。
- [x] full suite、privacy scan、2 service の実機起動、1 polling interval と pickup evidence を確認する。
- [ ] repository preflight PASSを確認する（既存Human Approval gateの人間確認待ち）。
- [x] branch を commit/push し Draft PR を作る。
