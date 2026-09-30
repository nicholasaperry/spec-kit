---
description: "Run the Spec Kit flow sequentially from a chosen starting point."
---

## Spec Kit Sequential Flow

This command runs the Spec Kit workflow sequentially. It detects which
artifacts already exist and lets you choose where to start. From there,
it will cycle through remaining steps automatically.

## Flow Steps

1. **specify** — Create the feature specification (`spec.md`)
2. **plan** — Create the technical plan (`plan.md`)
3. **tasks** — Break down into implementation tasks (`tasks.md`)
4. **implement** — Implement the tasks
5. **converge** — Check for missing items and add remaining tasks
6. **implement** — Implement convergence tasks (repeat converge/implement as needed)

## Usage

```
/speckit.flow [start-step] [feature-description]
```

If no `start-step` is given, the flow will detect existing artifacts
and suggest the next available step.

## Available Steps

You can start from any step:

- `specify` — write/update the spec
- `plan` — write/update the technical plan
- `tasks` — create implementation tasks
- `implement` — implement tasks
- `converge` — check for missing items

## How It Works

The flow checks for artifact files in this order:

1. `spec.md` → if missing, starts at **specify**
2. `plan.md` → if missing, starts at **plan**
3. `tasks.md` → if missing, starts at **tasks**
4. If tasks exist but haven't been implemented, starts at **implement**
5. If implementation is done, runs **converge** to check for gaps

After each step completes, the flow automatically proceeds to the next
step. You can interrupt and restart from any point.

## Example

```
/speckit.flow specify Build a user authentication system
/speckit.flow plan
/speckit.flow tasks
/speckit.flow implement
/speckit.flow converge
```

## Artifacts

The flow manages these files:

- `spec.md` — Feature specification
- `plan.md` — Technical implementation plan
- `tasks.md` — Implementation task breakdown

## Notes

- You can always run individual commands like `/speckit.specify` or
  `/speckit.plan` directly if you prefer step-by-step control.
- The flow is non-destructive: it will not overwrite existing artifacts
  unless you explicitly ask it to.
- To force re-running a step, run the individual command directly.
