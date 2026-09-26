---
tracker:
  kind: github
  provider:
    repo: "__REPOSITORY__"
    token: $GITHUB_TOKEN
  required_labels:
    - __ROUTING_LABEL__
    - __EXECUTION_TARGET_LABEL__
  active_states:
    - open
  terminal_states:
    - closed
polling:
  interval_ms: 30000
workspace:
  root: workspaces
hooks:
  after_create: |
    gh repo clone __REPOSITORY__ .
  before_run: |
    if [ -n "$(git status --porcelain --untracked-files=all)" ]; then
      exit 0
    fi
    default_branch="$(gh repo view __REPOSITORY__ --json defaultBranchRef --jq '.defaultBranchRef.name')"
    git fetch --prune origin "$default_branch"
    git reset --hard "origin/$default_branch"
agent:
  max_concurrent_agents: 1
  max_turns: 20
codex:
  command: codex app-server
  approval_policy: never
  thread_sandbox: workspace-write
---

You are working on {{ issue.identifier }}.

{{ issue.description }}

Work only on the approved Issue scope. Preserve verification evidence and report blockers rather than guessing.
Repository-native Project fields, approval gates, dependency checks, and execution/resource locks remain authoritative; routing labels alone are never authorization to bypass them.

Git publication policy for `workspace-write`:

- Codex `workspace-write` protects Git metadata under `.git`. Do not treat that protection as a repository permission failure, and do not use `danger-full-access` to bypass it.
- Do not run Git commands that mutate Git metadata from inside the Codex sandbox, including `git fetch`, `git pull`, `git checkout`, `git switch`, `git branch`, `git commit`, `git push`, `git merge`, or `git rebase`.
- The Symphony `before_run` hook refreshes a clean workspace to the current remote default branch outside the Codex sandbox. If the workspace already contains changes, the hook preserves them instead of resetting them.
- Use read-only Git commands such as `git status`, `git diff`, `git diff --check`, and `git rev-parse HEAD` for inspection and verification.
- Use Symphony's host-side `github_api` tool for GitHub writes. Before publishing, GET the repository/default branch ref and require its remote head SHA to equal the local `git rev-parse HEAD` base SHA. If they differ, stop and record a base-drift blocker instead of publishing.
- Publish only approved-scope changes. Use the Git Data REST API through `github_api` to create blobs for changed files, create a tree based on the verified base tree, create a commit whose parent is the verified base SHA, and create a task branch ref that points at that commit. Represent deletions explicitly in the tree. Use base64 blob encoding for binary files.
- Create a Draft PR through `github_api` from the task branch to the verified default branch, then write the branch, commit SHA, verification result, Draft PR URL, changed files, and residual risk to the Issue Workpad.
- Never force-update or reuse an unrelated existing branch. If the intended task branch already exists and safe ownership/ancestry cannot be proven, stop and record the conflict.
