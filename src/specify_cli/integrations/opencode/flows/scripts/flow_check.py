#!/usr/bin/env python3
"""Flow state helper for OpenCode sequential flow plugin.

Checks which Spec Kit artifacts exist and reports the current flow state.
Used by the flow orchestrator to determine where to start.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# Define the canonical flow order
FLOW_ORDER = [
    "specify",   # spec.md
    "plan",      # plan.md
    "tasks",     # tasks.md
    "implement", # implementation
    "converge",  # convergence check
]

# Map steps to their artifact files
STEP_ARTIFACTS = {
    "specify": ["spec.md"],
    "plan": ["plan.md"],
    "tasks": ["tasks.md"],
    "implement": [],  # no single artifact — checks for code changes
    "converge": [],   # no single artifact — checks for gaps
}


def check_artifact(project_root: Path, artifact: str) -> bool:
    """Check if an artifact file exists in the project root."""
    return (project_root / artifact).is_file()


def get_flow_state(project_root: Path) -> dict:
    """Get the current flow state based on existing artifacts.

    Returns a dict with:
    - completed_steps: list of step names that are done
    - next_step: the next step in the flow
    - all_steps: the full flow order
    - start_from: suggested starting point
    """
    completed = []
    for step in FLOW_ORDER:
        artifacts = STEP_ARTIFACTS[step]
        if not artifacts:
            # Steps without artifacts (implement, converge) are considered
            # "done" only if all previous steps with artifacts are complete
            if all(check_artifact(project_root, a) for a in STEP_ARTIFACTS.get(step, [])):
                if step in ("implement", "converge"):
                    # These are done if tasks.md exists and was completed
                    if "tasks" in completed:
                        completed.append(step)
                    else:
                        break
                else:
                    completed.append(step)
            else:
                break
        else:
            if all(check_artifact(project_root, a) for a in artifacts):
                completed.append(step)
            else:
                break

    # Determine next step
    next_step = None
    for step in FLOW_ORDER:
        if step not in completed:
            next_step = step
            break

    return {
        "completed_steps": completed,
        "next_step": next_step,
        "all_steps": FLOW_ORDER,
        "start_from": next_step or "complete",
    }


def main() -> None:
    """Main entry point for CLI usage."""
    if len(sys.argv) < 2:
        print("Usage: flow_check.py <project_root>", file=sys.stderr)
        sys.exit(1)

    project_root = Path(sys.argv[1])
    if not project_root.is_dir():
        print(f"Error: {project_root} is not a directory", file=sys.stderr)
        sys.exit(1)

    state = get_flow_state(project_root)
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
