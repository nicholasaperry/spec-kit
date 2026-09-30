"""OpenCode sequential flow plugin for Spec Kit.

Installs a ``speckit.flow.md`` command that orchestrates Spec Kit workflows
sequentially.  The flow detects which artifacts already exist, lets the user
pick a starting point, then cycles through remaining steps automatically.

The only "agents" in the flow are the actual steps (specify, plan, tasks,
implement, converge), so users can start anywhere and the flow will guide
them through the rest.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...manifest import IntegrationManifest
from .. import OpencodeIntegration


class FlowPlugin(OpencodeIntegration):
    """OpenCode plugin that installs sequential flow commands."""

    key = "opencode"  # shares the opencode integration
    config: dict[str, Any] = {}  # re-used from parent
    registrar_config: dict[str, Any] = {}  # re-used from parent

    FLOW_DIR = ".opencode/flows"

    @classmethod
    def flow_command_template(cls) -> str:
        """Return the main flow orchestrator command template."""
        return (
            '---\n'
            'description: "Run the Spec Kit flow sequentially from a chosen starting point."\n'
            '---\n'
            '\n'
            '## Spec Kit Sequential Flow\n'
            '\n'
            'This command runs the Spec Kit workflow sequentially.  It detects which\n'
            'artifacts already exist and lets you choose where to start.  From there,\n'
            'it will cycle through remaining steps automatically.\n'
            '\n'
            '## Flow Steps\n'
            '\n'
            '1. **specify** — Create the feature specification (``spec.md``)\n'
            '2. **plan** — Create the technical plan (``plan.md``)\n'
            '3. **tasks** — Break down into implementation tasks (``tasks.md``)\n'
            '4. **implement** — Implement the tasks\n'
            '5. **converge** — Check for missing items and add remaining tasks\n'
            '6. **implement** — Implement convergence tasks (repeat converge/implement as needed)\n'
            '\n'
            '## Usage\n'
            '\n'
            '```\n'
            '/speckit.flow [start-step] [feature-description]\n'
            '```\n'
            '\n'
            'If no ``start-step`` is given, the flow will detect existing artifacts\n'
            'and suggest the next available step.\n'
            '\n'
            '## Available Steps\n'
            '\n'
            'You can start from any step:\n'
            '\n'
            '- ``specify`` — write/update the spec\n'
            '- ``plan`` — write/update the technical plan\n'
            '- ``tasks`` — create implementation tasks\n'
            '- ``implement`` — implement tasks\n'
            '- ``converge`` — check for missing items\n'
            '\n'
            '## How It Works\n'
            '\n'
            'The flow checks for artifact files in this order:\n'
            '\n'
            '1. ``spec.md`` → if missing, starts at **specify**\n'
            '2. ``plan.md`` → if missing, starts at **plan**\n'
            '3. ``tasks.md`` → if missing, starts at **tasks**\n'
            '4. If tasks exist but haven\'t been implemented, starts at **implement**\n'
            '5. If implementation is done, runs **converge** to check for gaps\n'
            '\n'
            'After each step completes, the flow automatically proceeds to the next\n'
            'step.  You can interrupt and restart from any point.\n'
            '\n'
            '## Example\n'
            '\n'
            '```\n'
            '/speckit.flow specify Build a user authentication system\n'
            '/speckit.flow plan\n'
            '/speckit.flow tasks\n'
            '/speckit.flow implement\n'
            '/speckit.flow converge\n'
            '```\n'
            '\n'
            '## Artifacts\n'
            '\n'
            'The flow manages these files:\n'
            '\n'
            '- ``spec.md`` — Feature specification\n'
            '- ``plan.md`` — Technical implementation plan\n'
            '- ``tasks.md`` — Implementation task breakdown\n'
            '\n'
            '## Notes\n'
            '\n'
            '- You can always run individual commands like ``/speckit.specify`` or\n'
            '  ``/speckit.plan`` directly if you prefer step-by-step control.\n'
            '- The flow is non-destructive: it will not overwrite existing artifacts\n'
            '  unless you explicitly ask it to.\n'
            '- To force re-running a step, run the individual command directly.\n'
        )

    @classmethod
    def flow_state_template(cls) -> str:
        """Return the flow state tracking file template."""
        return (
            '{\n'
            '  "version": 1,\n'
            '  "current_step": null,\n'
            '  "completed_steps": [],\n'
            '  "feature_description": "",\n'
            '  "started_at": null,\n'
            '  "completed_at": null\n'
            '}\n'
        )

    def install_flow_plugin(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
    ) -> list[Path]:
        """Install the flow plugin files into the project.

        Creates:
        - ``.opencode/commands/speckit.flow.md`` — Flow orchestrator command
        - ``.opencode/flows/flow-state.json`` — Flow state tracker (on first run)

        Returns the list of files created.
        """
        created: list[Path] = []

        # Install the flow command
        dest_dir = self.commands_dest(project_root)
        flow_cmd_path = dest_dir / "speckit.flow.md"

        content = self.flow_command_template()
        self.write_file_and_record(content, flow_cmd_path, project_root, manifest)
        created.append(flow_cmd_path)

        # Create the flows directory (state file is created on first run)
        flows_dir = project_root / self.FLOW_DIR
        flows_dir.mkdir(parents=True, exist_ok=True)

        return created

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Override setup to also install the flow plugin."""
        # First, run the parent setup (standard commands)
        created = super().setup(project_root, manifest, parsed_options, **opts)

        # Then install the flow plugin
        flow_created = self.install_flow_plugin(project_root, manifest)
        created.extend(flow_created)

        return created

    def teardown(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        force: bool = False,
    ) -> list[Path]:
        """Override teardown to also remove flow plugin files."""
        removed = super().teardown(project_root, manifest, force)

        # Remove flow command if tracked
        flow_cmd = project_root / ".opencode" / "commands" / "speckit.flow.md"
        if flow_cmd.exists():
            # Only remove if it was installed by us (check for our marker)
            content = flow_cmd.read_text(encoding="utf-8")
            if "Spec Kit Sequential Flow" in content:
                flow_cmd.unlink()
                rel = flow_cmd.resolve().relative_to(project_root.resolve())
                manifest.remove(rel)
                removed.append(flow_cmd)

        return removed
