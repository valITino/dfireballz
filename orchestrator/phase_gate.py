"""Phase gating for the canonical forensic process model.

Pure logic — no DB, no async, no I/O. The runner uses this to decide
whether a playbook step is allowed at the current point in the
investigation, and to classify forward progress vs. loopback.

Canonical phase order (see ``docs/forensic-process.md``):

    readiness → identification → acquisition →
    examination → analysis → reporting

Soft mode (default): every step is allowed; loopbacks (steps tagged with
an earlier phase than the highest-reached phase) are recorded as
documented loopback events. Steps without a phase tag inherit the
current phase and emit a warning.

Strict mode: out-of-order steps are rejected unless an explicit
``loopback_reason`` accompanies the run. Untagged steps are rejected.
Unknown phase values are rejected in both modes — they would defeat
the whole point of the model.
"""

from __future__ import annotations

from dataclasses import dataclass, field

PHASE_ORDER: tuple[str, ...] = (
    "readiness",
    "identification",
    "acquisition",
    "examination",
    "analysis",
    "reporting",
)

VALID_PHASES = frozenset(PHASE_ORDER)


def phase_index(phase: str) -> int:
    """Return the ordinal of ``phase`` in the canonical sequence.

    Raises ``ValueError`` for unknown phase names.
    """
    try:
        return PHASE_ORDER.index(phase)
    except ValueError as exc:
        raise ValueError(
            f"unknown phase {phase!r}; expected one of {list(PHASE_ORDER)}"
        ) from exc


@dataclass(frozen=True)
class StepDecision:
    """Result of evaluating one playbook step against the phase gate."""

    action: str  # "advance" | "same" | "loopback" | "reject" | "warn"
    step_phase: str | None
    from_phase: str | None  # the phase the gate was at before this step
    to_phase: str | None  # the phase the gate is at after this step (==step_phase if accepted)
    reason: str = ""

    @property
    def accepted(self) -> bool:
        return self.action in {"advance", "same", "loopback", "warn"}

    @property
    def rejected(self) -> bool:
        return self.action == "reject"


@dataclass
class PhaseGate:
    """Stateful phase tracker for one playbook run.

    Track ``current_phase`` (highest phase reached so far) and a log of
    loopback events. A new gate starts before any phase has been
    entered (``current_phase is None``).
    """

    current_phase: str | None = None
    loopbacks: list[dict[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def evaluate(
        self,
        step_phase: str | None,
        *,
        strict: bool,
        loopback_reason: str | None = None,
    ) -> StepDecision:
        """Decide whether this step is allowed at the current point.

        Does not mutate the gate — call :meth:`apply` to commit the
        decision once the runner has acted on it.
        """
        from_phase = self.current_phase

        if step_phase is None:
            if strict:
                return StepDecision(
                    action="reject",
                    step_phase=None,
                    from_phase=from_phase,
                    to_phase=from_phase,
                    reason=(
                        "step has no `phase` tag and strict mode is on; "
                        "tag the step in the playbook YAML"
                    ),
                )
            return StepDecision(
                action="warn",
                step_phase=None,
                from_phase=from_phase,
                to_phase=from_phase,
                reason="step has no `phase` tag — inheriting current phase",
            )

        if step_phase not in VALID_PHASES:
            return StepDecision(
                action="reject",
                step_phase=step_phase,
                from_phase=from_phase,
                to_phase=from_phase,
                reason=(
                    f"unknown phase {step_phase!r}; "
                    f"expected one of {list(PHASE_ORDER)}"
                ),
            )

        # First step ever — accept and seed current_phase.
        if from_phase is None:
            return StepDecision(
                action="advance",
                step_phase=step_phase,
                from_phase=None,
                to_phase=step_phase,
            )

        cur_idx = phase_index(from_phase)
        new_idx = phase_index(step_phase)

        if new_idx == cur_idx:
            return StepDecision(
                action="same",
                step_phase=step_phase,
                from_phase=from_phase,
                to_phase=from_phase,
            )

        if new_idx > cur_idx:
            return StepDecision(
                action="advance",
                step_phase=step_phase,
                from_phase=from_phase,
                to_phase=step_phase,
            )

        # new_idx < cur_idx — loopback
        if strict and not loopback_reason:
            return StepDecision(
                action="reject",
                step_phase=step_phase,
                from_phase=from_phase,
                to_phase=from_phase,
                reason=(
                    f"loopback from {from_phase!r} to {step_phase!r} "
                    "blocked by strict mode (provide loopback_reason)"
                ),
            )
        return StepDecision(
            action="loopback",
            step_phase=step_phase,
            from_phase=from_phase,
            to_phase=step_phase,
            reason=loopback_reason or "(soft mode loopback — no reason given)",
        )

    def apply(self, decision: StepDecision) -> None:
        """Commit an accepted decision to the gate's state.

        Idempotent for ``same``-action decisions. ``reject`` decisions
        are a no-op (the runner should not call apply on a reject).
        """
        if decision.action == "reject":
            return
        if decision.action == "warn":
            self.warnings.append(decision.reason)
            return
        if decision.action == "loopback":
            self.loopbacks.append(
                {
                    "from_phase": decision.from_phase or "",
                    "to_phase": decision.to_phase or "",
                    "reason": decision.reason,
                }
            )
            # Loopback drops the gate back to the target phase so the
            # runner's audit trail reflects the new starting point.
            self.current_phase = decision.to_phase
            return
        # advance | same
        if decision.to_phase is not None:
            self.current_phase = decision.to_phase

    def summary(self) -> dict:
        """Return a JSON-serializable summary of the gate's history."""
        return {
            "final_phase": self.current_phase,
            "loopbacks": list(self.loopbacks),
            "warnings": list(self.warnings),
        }


__all__ = [
    "PHASE_ORDER",
    "PhaseGate",
    "StepDecision",
    "VALID_PHASES",
    "phase_index",
]
