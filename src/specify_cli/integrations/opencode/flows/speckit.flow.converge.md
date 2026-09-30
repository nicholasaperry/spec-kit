---
description: "Flow step: Check for missing items and add remaining tasks (converge)."
---

## Flow Step: Converge

This is the **converge** step of the Spec Kit sequential flow.

Check for missing items and add any remaining tasks.

## Instructions

1. Check if `tasks.md` exists (required prerequisite)
2. If not, redirect to the tasks step
3. Run the full `/speckit.converge` command to check for gaps
4. If new tasks are added, proceed back to the **implement** step
5. If no new tasks are found, the flow is complete

## Completion

After this step completes:
- If new tasks were added, the flow loops back to **implement**
- If no new tasks were found, the flow is complete

## Artifact

- `tasks.md` — May be updated with additional tasks
