# Repository / Issue integration

Excellent-Nd installation has three levels:

1. Install the ChatGPT Skill.
2. Integrate Excellent-Nd with the target repository's existing Issue workflow.
3. Install the execution host runtime.

Prefer doing level 2 from ChatGPT. Ask ChatGPT to inspect existing labels, Issue templates/forms, GitHub Actions/bots, status/routing conventions, and any existing `.excellent-nd/repository.json`.

If the repository has no conflicting Issue workflow, use the standard mapping. If existing conventions exist, ChatGPT should propose one mapping for confirmation rather than asking the operator to configure labels one by one.

Existing labels may be reused only when their semantics are verified. `management: existing` means Excellent-Nd must not create or modify the label. `management: excellent-nd` means create it only when missing and never overwrite an existing label.

Approved mappings are stored in `.excellent-nd/repository.json`. Execution-host setup fails closed until labels, templates, and automation reviews are confirmed.

Existing Issue templates normally remain unchanged because ChatGPT creates the complete Excellent-Nd Issue body directly.


## Generic mapping and dispatch gates

Excellent-Nd does not replace a repository's native workflow model. Core states remain `scheduled / running / blocked / review`. Repository-specific field names and status values are configuration.

Use `dispatch_gates[]` to combine GitHub Project fields, labels, and Issue state. Fields such as Agent or Human Approval are optional repository rules, not Excellent-Nd requirements.

For GitHub Project status authority, map Excellent-Nd runtime events to the repository's existing status options with `status_integration.event_mapping`. Only events listed in `mutable_events` may be changed automatically.

The public generic example is `config/repository-config.github-project.example.json`. Do not copy private repository names, internal project titles, or identifying workflow values into public examples, Issues, PRs, or release artifacts.
