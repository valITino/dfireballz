"""Tests for orchestrator.phase_gate — pure-logic phase gating."""

import pytest
from phase_gate import (
    PHASE_ORDER,
    PhaseGate,
    StepDecision,
    phase_index,
)


def test_phase_order_is_canonical():
    assert PHASE_ORDER == (
        "readiness",
        "identification",
        "acquisition",
        "examination",
        "analysis",
        "reporting",
    )


def test_phase_index_known():
    assert phase_index("readiness") == 0
    assert phase_index("reporting") == 5


def test_phase_index_unknown_raises():
    with pytest.raises(ValueError, match="unknown phase"):
        phase_index("not-a-phase")


def test_first_step_advances_from_none():
    gate = PhaseGate()
    d = gate.evaluate("readiness", strict=False)
    assert d.action == "advance"
    assert d.from_phase is None
    assert d.to_phase == "readiness"
    gate.apply(d)
    assert gate.current_phase == "readiness"


def test_forward_advance():
    gate = PhaseGate(current_phase="acquisition")
    d = gate.evaluate("examination", strict=True)
    assert d.action == "advance"
    assert d.to_phase == "examination"
    gate.apply(d)
    assert gate.current_phase == "examination"


def test_same_phase_multi_step_allowed():
    gate = PhaseGate(current_phase="examination")
    d = gate.evaluate("examination", strict=True)
    assert d.action == "same"
    assert d.from_phase == "examination"
    assert d.to_phase == "examination"
    gate.apply(d)
    assert gate.current_phase == "examination"


def test_loopback_soft_mode_records_event():
    gate = PhaseGate(current_phase="analysis")
    d = gate.evaluate("examination", strict=False)
    assert d.action == "loopback"
    assert d.from_phase == "analysis"
    assert d.to_phase == "examination"
    gate.apply(d)
    assert gate.current_phase == "examination"
    assert len(gate.loopbacks) == 1
    assert gate.loopbacks[0]["from_phase"] == "analysis"
    assert gate.loopbacks[0]["to_phase"] == "examination"


def test_loopback_strict_without_reason_rejected():
    gate = PhaseGate(current_phase="analysis")
    d = gate.evaluate("examination", strict=True)
    assert d.action == "reject"
    assert "loopback" in d.reason
    assert "strict" in d.reason
    # Apply on reject is a no-op.
    gate.apply(d)
    assert gate.current_phase == "analysis"
    assert gate.loopbacks == []


def test_loopback_strict_with_reason_allowed():
    gate = PhaseGate(current_phase="analysis")
    d = gate.evaluate(
        "examination",
        strict=True,
        loopback_reason="Found new evidence source mid-analysis",
    )
    assert d.action == "loopback"
    assert d.reason == "Found new evidence source mid-analysis"
    gate.apply(d)
    assert gate.current_phase == "examination"
    assert gate.loopbacks[0]["reason"] == "Found new evidence source mid-analysis"


def test_untagged_step_strict_rejected():
    gate = PhaseGate(current_phase="examination")
    d = gate.evaluate(None, strict=True)
    assert d.action == "reject"
    assert "no `phase` tag" in d.reason


def test_untagged_step_soft_warns_inherits_phase():
    gate = PhaseGate(current_phase="examination")
    d = gate.evaluate(None, strict=False)
    assert d.action == "warn"
    assert d.to_phase == "examination"  # inherits
    gate.apply(d)
    assert gate.current_phase == "examination"
    assert len(gate.warnings) == 1


def test_unknown_phase_rejected_in_both_modes():
    gate = PhaseGate(current_phase="examination")
    for strict in (True, False):
        d = gate.evaluate("magic", strict=strict)
        assert d.action == "reject"
        assert "unknown phase" in d.reason


def test_full_canonical_sequence_strict():
    gate = PhaseGate()
    for phase in PHASE_ORDER:
        d = gate.evaluate(phase, strict=True)
        assert d.action == "advance"
        gate.apply(d)
    assert gate.current_phase == "reporting"
    assert gate.loopbacks == []


def test_summary_shape():
    gate = PhaseGate()
    for p in ("readiness", "identification", "acquisition", "examination"):
        d = gate.evaluate(p, strict=False)
        gate.apply(d)
    # Loopback to acquisition.
    d = gate.evaluate("acquisition", strict=False, loopback_reason="re-image")
    gate.apply(d)
    s = gate.summary()
    assert s["final_phase"] == "acquisition"
    assert len(s["loopbacks"]) == 1
    assert s["loopbacks"][0]["reason"] == "re-image"
    assert s["warnings"] == []


def test_decision_helpers():
    accepted = StepDecision(
        action="advance", step_phase="readiness", from_phase=None, to_phase="readiness"
    )
    assert accepted.accepted is True
    assert accepted.rejected is False

    rejected = StepDecision(
        action="reject", step_phase=None, from_phase=None, to_phase=None
    )
    assert rejected.accepted is False
    assert rejected.rejected is True
