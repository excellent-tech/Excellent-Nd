# Version policy

Maintain two conceptual channels.

## Validated stable channel

Use an exact, tested version set for normal work:

- Symphony exact release/version
- Codex CLI/App Server exact version when practical
- WORKFLOW/config revision
- Excellent-Nd Skill revision

Do not automatically upgrade simply because a newer stable release exists.

Promote a new set only after validation.

## Development channel

Allow a separate development profile to evaluate newer stable releases, nightly builds, or development versions without changing the validated stable profile.

Do not use an unvalidated development profile for important work.

## Upgrade validation

For an optional upgrade, run the relevant regression subset based on changed components.

For a forced/mandatory upgrade, run the full V1 regression suite before promoting it to the validated stable channel. The full suite should include:

1. single Task end-to-end;
2. multiple Task parallel execution;
3. fixed execution-target routing;
4. same-Task continuation;
5. blocked → human decision → continuation;
6. PR creation/update and review state;
7. result import back into ChatGPT;
8. Issue machine-readable schema compatibility;
9. account usage/rate-limit handling;
10. process restart/recovery behavior.

After validation, promote the exact tested version set. Keep the prior validated set available for rollback when possible.
