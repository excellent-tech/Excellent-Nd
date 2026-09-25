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
