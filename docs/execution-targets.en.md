# execution_target and execution-host inventory

This document defines how a repository manages 0..N Excellent-Nd execution hosts, including registration, disablement, removal, and re-registration.

## 1. When a host becomes registered

Registration has two stages.

1. **Create a local registration candidate**  
   `scripts/setup.py` verifies prerequisites, GitHub authentication, Symphony checksum, Codex compatibility, generated WORKFLOW, and routing labels. Only after smoke verification passes does it create or update `.excellent-nd/targets/<target-id>.json`.
2. **Publish the shared registration**  
   Review the generated target file, commit and push it, and merge it into the operational branch (normally main). From that point ChatGPT, humans, and other execution hosts can read the same inventory through GitHub.

Setup does not automatically commit or push the record. `enabled: true` means the host is configured and eligible for assignment; it is not an online heartbeat.

## 2. Register the first host

Run from the repository root:

```bash
python3 scripts/setup.py \
  --repo OWNER/REPOSITORY \
  --repo-path . \
  --prefix .excellent-nd \
  --skill-confirmed
```

The local hostname is the default target ID. Use an explicit alias when the hostname should not be committed.

After smoke PASS, review and commit `.excellent-nd/targets/<target-id>.json`. With branch protection, merge it through a PR. Shared registration is complete only after that Git change is accepted.

## 3. Register additional hosts

Run the same setup on each host. The inventory uses one file per host:

```text
.excellent-nd/targets/
├─ worker-a.json
├─ worker-b.json
└─ worker-c.json
```

Each Symphony profile requires both `symphony-ready` and its own `nd-target:<id>`. Only the matching host can dispatch the Issue.

Do not keep a fixed host count. Derive registered hosts from the files and assignment candidates from records with `enabled: true`.

```bash
python3 scripts/target_inventory.py list --repo-root .
```

## 4. Temporarily disable a host

Do not delete the file first.

1. Change `enabled` to `false`.
2. Commit / push / merge that change so ChatGPT stops selecting the host for new Tasks.
3. Inspect open Issues targeting that host.
4. Finish them, block them, or checkpoint them into successor Issues.
5. Stop the Symphony profile/runtime as appropriate.

Never rewrite an existing Issue's `execution_target`. A move to another host uses a successor Issue.

## 5. Remove a host

Use **disable -> drain -> delete**.

1. Publish `enabled: false`.
2. Confirm there are no active Tasks for the target.
3. Stop the host runtime/profile.
4. Delete and commit the target record:

```bash
git rm .excellent-nd/targets/worker-b.json
git commit -m "ops: remove Excellent-Nd target worker-b"
git push
```

5. Merge through a PR where required.
6. Optionally remove host-local runtime state after audit/rollback checks.

Keep the `nd-target:<id>` GitHub label by default so historical Issues remain understandable. Remove it only as an explicit cleanup decision.

## 6. Re-register or rename

To re-register the same target, rerun setup, let smoke pass, then review and commit the regenerated record.

If the identity itself changes, register a new target, disable the old target, migrate unfinished work using checkpointed successor Issues, then remove the old record. Do not rename the target on existing Issues.

## 7. Inventory data

Store only non-credential routing/capacity metadata: target ID, hostname, enabled state, concurrency capacity, verification timestamp, and routing label. Never store tokens, passwords, API keys, private keys, or credentials.

## 8. ChatGPT assignment rules

ChatGPT does not assume a fixed number of machines. It reads `.excellent-nd/targets/*.json`, uses only `enabled: true` records for new assignments, proposes the sole candidate when exactly one exists, and plans allocation when multiple candidates exist. With zero candidates, it keeps the Task non-dispatchable.
