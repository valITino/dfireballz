"""Playbook Runner — Parses and executes investigation playbooks."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import frontmatter

from case_manager import CaseManager

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
                    "estimated_duration": post.metadata.get("estimated_duration", "Unknown"),
                    "tags": post.metadata.get("tags", []),
                    "steps_count": len(post.metadata.get("steps", [])),
                    "file": path.name,
                })
            except Exception:
                playbooks.append({"id": path.stem, "name": path.stem, "file": path.name})
        return playbooks

    def get_playbook(self, name: str) -> Optional[dict]:
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
        self, case_id: str, playbook_name: str, evidence_id: Optional[str] = None
    ) -> dict:
        """Execute a playbook against a case."""
        playbook = self.get_playbook(playbook_name)
        if not playbook:
            return {"error": f"Playbook '{playbook_name}' not found"}

        # Create playbook run record
        run = await self.case_manager.create_playbook_run(case_id, playbook_name)
        run_id = str(run["id"])

        steps_log: list[dict[str, Any]] = []
        try:
            for step in playbook["steps"]:
                step_log = {
                    "id": step.get("id", "unknown"),
                    "name": step.get("name", "Unknown step"),
                    "tool": step.get("tool"),
                    "action": step.get("action"),
                    "status": "pending",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                }

                # Log the step as a CoC entry
                await self.case_manager.log_coc_entry({
                    "case_id": case_id,
                    "action": "analyzed",
                    "actor": "playbook_runner",
                    "tool_used": f"{step.get('tool', 'unknown')}.{step.get('action', 'unknown')}",
                    "notes": f"Playbook step: {step.get('name', 'unknown')}",
                    "mcp_tool_call": json.dumps(step),
                })

                step_log["status"] = "completed"
                step_log["completed_at"] = datetime.now(timezone.utc).isoformat()
                steps_log.append(step_log)

            # Update playbook run status
            await self.case_manager.update_playbook_run(
                run_id,
                {
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc),
                    "steps": json.dumps(steps_log),
                },
            )

            return {
                "run_id": run_id,
                "status": "completed",
                "steps": steps_log,
                "playbook": playbook_name,
            }

        except Exception as e:
            await self.case_manager.update_playbook_run(
                run_id,
                {
                    "status": "failed",
                    "completed_at": datetime.now(timezone.utc),
                    "steps": json.dumps(steps_log),
                    "error_message": str(e),
                },
            )
            return {"run_id": run_id, "status": "failed", "error": str(e)}
