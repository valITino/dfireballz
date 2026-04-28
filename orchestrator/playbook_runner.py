"""Playbook Runner — Parses and executes investigation playbooks.

Phase gating: each playbook step may carry a ``phase`` tag matching one
of the canonical phases in ``docs/forensic-process.md``. The runner
tracks current phase as it iterates and classifies each step as
advance / same / loopback / warn / reject. In **soft mode** (default)
loopbacks are recorded as documented events but allowed; in **strict
mode** out-of-order steps are rejected unless an explicit
``loopback_reason`` accompanies the run.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import frontmatter
from case_manager import CaseManager
from phase_gate import PhaseGate

PLAYBOOKS_DIR = Path("/app/playbooks")


class PlaybookRunner:
    """Parses playbook Markdown files and orchestrates execution."""

    def __init__(self, case_manager: CaseManager):
        self.case_manager = case_manager

    def list_playbooks(self) -> list[dict]:
        """List all available playbooks with metadata."""
        playbooks = []
        for path in sorted(PLAYBOOKS_DIR.glob("*.md")):
            if path.name == "README.md":
                continue
            try:
                post = frontmatter.load(str(path))
                playbooks.append({
                    "id": post.metadata.get("id", path.stem),
                    "name": post.metadata.get("name", path.stem),
                    "description": post.metadata.get("description", ""),
                    "case_types": post.metadata.get("case_types", []),
                    "tools_required": post.metadata.get("tools_required", []),
                    "estimated_duration": post.metadata.get(
                        "estimated_duration", "Unknown"
                    ),
                    "tags": post.metadata.get("tags", []),
                    "process_model": post.metadata.get("process_model"),
                    "phases": post.metadata.get("phases", []),
                    "steps_count": len(post.metadata.get("steps", [])),
                    "file": path.name,
                })
            except Exception:
                playbooks.append({"id": path.stem, "name": path.stem, "file": path.name})
        return playbooks

    def get_playbook(self, name: str) -> dict | None:
        """Load a playbook by name or ID."""
        for path in PLAYBOOKS_DIR.glob("*.md"):
            if path.name == "README.md":
                continue
            try:
                post = frontmatter.load(str(path))
                if post.metadata.get("id") == name or path.stem == name:
                    return {
                        "metadata": post.metadata,
                        "content": post.content,
                        "steps": post.metadata.get("steps", []),
                    }
            except Exception:
                continue
        return None

    async def run(
        self,
        case_id: str,
        playbook_name: str,
        *,
        strict: bool = False,
        loopback_reason: str | None = None,
    ) -> dict:
        """Execute a playbook against a case.

        Args:
            case_id: Case UUID.
            playbook_name: Playbook ID or filename stem.
            strict: If True, refuse out-of-order steps and untagged steps.
            loopback_reason: Required in strict mode for any step that
                loops back to an earlier phase. Recorded on every
                loopback CoC entry produced by the run.
        """
        playbook = self.get_playbook(playbook_name)
        if not playbook:
            return {"error": f"Playbook '{playbook_name}' not found"}

        # Create playbook run record
        run = await self.case_manager.create_playbook_run(case_id, playbook_name)
        run_id = str(run["id"])

        gate = PhaseGate()
        steps_log: list[dict[str, Any]] = []
        rejected_step: dict[str, Any] | None = None

        try:
            for step in playbook["steps"]:
                step_phase = step.get("phase")
                decision = gate.evaluate(
                    step_phase,
                    strict=strict,
                    loopback_reason=loopback_reason,
                )

                step_log: dict[str, Any] = {
                    "id": step.get("id", "unknown"),
                    "name": step.get("name", "Unknown step"),
                    "tool": step.get("tool"),
                    "action": step.get("action"),
                    "phase": step_phase,
                    "phase_decision": decision.action,
                    "phase_from": decision.from_phase,
                    "phase_to": decision.to_phase,
                    "phase_reason": decision.reason,
                    "status": "pending",
                    "started_at": datetime.now(UTC).isoformat(),
                }

                if decision.rejected:
                    step_log["status"] = "rejected"
                    step_log["completed_at"] = datetime.now(UTC).isoformat()
                    steps_log.append(step_log)
                    rejected_step = step_log
                    # Also log the rejection to chain of custody so the
                    # legal record reflects that a step was blocked.
                    await self.case_manager.log_coc_entry({
                        "case_id": case_id,
                        "action": "rejected",
                        "actor": "playbook_runner",
                        "tool_used": (
                            f"{step.get('tool', 'unknown')}."
                            f"{step.get('action', 'unknown')}"
                        ),
                        "notes": (
                            f"Playbook step rejected by phase gate "
                            f"(strict={strict}): {decision.reason}"
                        ),
                        "mcp_tool_call": json.dumps(step),
                    })
                    break

                gate.apply(decision)

                # Build the CoC notes string with phase context.
                phase_note = (
                    f"phase={decision.action}:{decision.to_phase}"
                    if decision.to_phase
                    else f"phase={decision.action}"
                )
                if decision.action == "loopback":
                    phase_note += (
                        f" (from {decision.from_phase}; reason: {decision.reason})"
                    )
                elif decision.action == "warn" and decision.reason:
                    phase_note += f" ({decision.reason})"

                await self.case_manager.log_coc_entry({
                    "case_id": case_id,
                    "action": "analyzed",
                    "actor": "playbook_runner",
                    "tool_used": f"{step.get('tool', 'unknown')}.{step.get('action', 'unknown')}",
                    "notes": (
                        f"Playbook step: {step.get('name', 'unknown')} | {phase_note}"
                    ),
                    "mcp_tool_call": json.dumps(step),
                })

                step_log["status"] = "completed"
                step_log["completed_at"] = datetime.now(UTC).isoformat()
                steps_log.append(step_log)

            phase_summary = gate.summary()
            final_status = "rejected" if rejected_step else "completed"

            await self.case_manager.update_playbook_run(
                run_id,
                {
                    "status": final_status,
                    "completed_at": datetime.now(UTC),
                    "steps": json.dumps(steps_log),
                },
            )

            return {
                "run_id": run_id,
                "status": final_status,
                "steps": steps_log,
                "playbook": playbook_name,
                "strict": strict,
                "phase_summary": phase_summary,
                **({"rejected_step": rejected_step["id"]} if rejected_step else {}),
            }

        except Exception as e:
            await self.case_manager.update_playbook_run(
                run_id,
                {
                    "status": "failed",
                    "completed_at": datetime.now(UTC),
                    "steps": json.dumps(steps_log),
                    "error_message": str(e),
                },
            )
            return {"run_id": run_id, "status": "failed", "error": str(e)}
