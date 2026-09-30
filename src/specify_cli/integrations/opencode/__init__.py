"""opencode integration."""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ..base import MarkdownIntegration
from ..manifest import IntegrationManifest


class OpencodeIntegration(MarkdownIntegration):
    key = "opencode"
    config = {
        "name": "opencode",
        "folder": ".opencode/",
        "commands_subdir": "commands",
        "install_url": "https://opencode.ai",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".opencode/commands",
        "legacy_dir": ".opencode/command",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }

    CANONICAL_TO_NATIVE = {
        "pre_tool_use": "tool.execute.before",
        "post_tool_use": "tool.execute.after",
        # session_start maps to the system-prompt transform hook (not the
        # session.created event) so the handler's stdout is injected into the
        # system prompt — session.created has no output channel. The hook
        # fires per LLM request, which keeps the context present across
        # compaction at the cost of running the handler per turn.
        "session_start": "experimental.chat.system.transform",
        # user_prompt_submit maps to chat.message so handler stdout is
        # injected as a synthetic text part on the user's message.
        "user_prompt_submit": "chat.message",
        "session_end": "session.deleted",
    }
    events_config_file = "opencode.json"
    events_format = "ts-plugin"

    # -- Flow plugin --------------------------------------------------------

    FLOW_DIR = ".opencode/flows"
    FLOW_SCRIPTS_DIR = ".specify/integrations/opencode/flows/scripts"

    FLOW_COMMANDS = {
        "speckit.flow": "speckit.flow.md",
        "speckit.flow.specify": "speckit.flow.specify.md",
        "speckit.flow.plan": "speckit.flow.plan.md",
        "speckit.flow.tasks": "speckit.flow.tasks.md",
        "speckit.flow.implement": "speckit.flow.implement.md",
        "speckit.flow.converge": "speckit.flow.converge.md",
    }

    def _flow_scripts_dir(self) -> Path | None:
        """Return path to the flow plugin's bundled scripts directory."""
        import inspect

        cls_file = Path(inspect.getfile(type(self))).resolve().parent / "flows" / "scripts"
        return cls_file if cls_file.is_dir() else None

    def _install_flow_commands(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
    ) -> list[Path]:
        """Install the flow plugin commands into the project."""
        import shutil

        created: list[Path] = []
        dest_dir = self.commands_dest(project_root)

        # Resolve the flow templates directory (sibling of this module's flows/)
        import inspect
        flows_dir = Path(inspect.getfile(type(self))).resolve().parent / "flows"

        for cmd_name, template_file in self.FLOW_COMMANDS.items():
            src = flows_dir / template_file
            if not src.is_file():
                continue
            dest = dest_dir / f"{cmd_name}.md"
            shutil.copy2(src, dest)
            # Record in manifest
            rel = dest.resolve().relative_to(project_root.resolve())
            manifest.record_existing(rel)
            created.append(dest)

        # Install flow check script
        scripts_src = self._flow_scripts_dir()
        if scripts_src:
            scripts_dest = project_root / self.FLOW_SCRIPTS_DIR
            scripts_dest.mkdir(parents=True, exist_ok=True)
            for src_script in sorted(scripts_src.iterdir()):
                if not src_script.is_file():
                    continue
                dst_script = scripts_dest / src_script.name
                shutil.copy2(src_script, dst_script)
                if dst_script.suffix in (".sh", ".py"):
                    dst_script.chmod(dst_script.stat().st_mode | 0o111)
                rel = dst_script.resolve().relative_to(project_root.resolve())
                manifest.record_existing(rel)
                created.append(dst_script)

        return created

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install standard commands plus the flow plugin."""
        # Run parent setup (standard commands)
        created = super().setup(project_root, manifest, parsed_options, **opts)

        # Install flow plugin commands
        flow_created = self._install_flow_commands(project_root, manifest)
        created.extend(flow_created)

        return created

    def teardown(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        force: bool = False,
    ) -> list[Path]:
        """Remove standard commands and flow plugin files."""
        removed = super().teardown(project_root, manifest, force)

        # Remove flow commands if they exist
        import inspect

        dest_dir = self.commands_dest(project_root)
        for cmd_name in self.FLOW_COMMANDS:
            flow_cmd = dest_dir / f"{cmd_name}.md"
            if flow_cmd.exists():
                # Check if it's one of ours by looking for our marker
                content = flow_cmd.read_text(encoding="utf-8")
                if "Spec Kit Sequential Flow" in content or "Flow Step:" in content:
                    flow_cmd.unlink()
                    rel = flow_cmd.resolve().relative_to(project_root.resolve())
                    manifest.remove(rel)
                    removed.append(flow_cmd)

        # Remove flow scripts
        scripts_dest = project_root / self.FLOW_SCRIPTS_DIR
        if scripts_dest.is_dir():
            import shutil

            for f in scripts_dest.iterdir():
                if f.is_file():
                    f.unlink()
                    rel = f.resolve().relative_to(project_root.resolve())
                    manifest.remove(rel)
            rel = scripts_dest.resolve().relative_to(project_root.resolve())
            manifest.remove(rel)
            removed.append(scripts_dest)

        return removed

    # -- CLI dispatch -------------------------------------------------------

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
        integration_args: Sequence[str] | None = None,
        integration_options: Mapping[str, Any] | None = None,
        project_root: Path | None = None,
    ) -> list[str] | None:
        self.validate_runtime_config(integration_args, integration_options)
        args = [self._resolve_executable(), "run"]
        # Apply operator-injected extra args before the prompt-derived
        # --command and the canonical --format/-m flags so Spec Kit's
        # later appends remain authoritative under repeated-flag CLI
        # semantics.
        self._apply_extra_args_env_var(args)

        message = prompt
        if prompt.startswith("/"):
            command, _, remainder = prompt[1:].partition(" ")
            if command:
                args.extend(["--command", command])
                message = remainder

        if model:
            args.extend(["-m", model])
        if output_json:
            args.extend(["--format", "json"])
        if message:
            args.append(message)
        return args
