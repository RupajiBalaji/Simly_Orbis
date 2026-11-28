"""
Spec-driven AI context builders & prompt-injection containment (P7-T2).

Guarantees:
1. Context is built strictly from the active experiment spec and the single
   target session_id — never reading or exposing other sessions' data.
2. All untrusted student text is sanitized and wrapped in explicit data-only
   delimiters with closing-tag neutralization.
"""

from __future__ import annotations

import re
from typing import Any

from app.lab.experiments import get_experiment
from app.lab.models import LabSession
from app.security import sanitize_text

_TAG_BREAKOUT_RE = re.compile(r"</?\s*(?:STUDENT_DATA_ONLY|SYSTEM|INSTRUCTIONS?|PROMPT)\s*>", re.IGNORECASE)


def wrap_untrusted_user_text(raw: str | None, max_length: int = 200) -> str:
    """Sanitize and isolate untrusted student text inside a data-only block."""
    cleaned = sanitize_text(raw, max_length)
    cleaned = _TAG_BREAKOUT_RE.sub("[filtered-tag]", cleaned)
    return f"<STUDENT_DATA_ONLY>\n{cleaned}\n</STUDENT_DATA_ONLY>"


def build_spec_mentor_context(session: LabSession) -> tuple[str, str, str]:
    """
    Build verified factual laboratory context strictly from the experiment spec
    and the single target LabSession.
    Returns (context_text, step_title, step_hint).
    """
    try:
        exp = get_experiment(session.experiment_id)
        step_idx = len(session.protocol_progress)
        if step_idx < len(exp.protocol):
            curr_step = exp.protocol[step_idx]
            raw_title = curr_step.get("title") or f"Step {step_idx + 1}"
            step_title = f"Step {step_idx + 1}: {raw_title}"
            step_hint = (
                curr_step.get("hint")
                or curr_step.get("hint_text")
                or "Follow standard laboratory safety protocols."
            )
            try:
                from app.routes.tutor import get_spec_mentor_hint  # noqa: PLC0415

                spec_h = get_spec_mentor_hint(session.experiment_id, step_id=curr_step.get("id"))
                if spec_h:
                    step_hint = spec_h
            except Exception:
                pass
        else:
            step_title = "Experiment Completed"
            step_hint = "All protocol steps completed. Ready to submit final lab report."
    except Exception:
        step_idx = len(session.protocol_progress)
        step_title = f"Step {step_idx + 1}: Protocol Step"
        step_hint = "Follow standard laboratory safety protocols."

    recent_events = session.events[-5:] if session.events else []
    events_str = "; ".join(e.get("message", "") for e in recent_events) or "Session initiated."
    violations_str = (
        "; ".join(f"{v.rule_id} {v.title} ({v.severity}): {v.explanation}" for v in session.violations)
        or "None (Clean safety record)."
    )
    ppe_str = ", ".join(sorted(session.ppe)) if session.ppe else "None"
    score_str = (
        f"Safety: {session.score_parts.get('safety', 0)}/40, "
        f"Accuracy: {session.score_parts.get('accuracy', 0)}/30, "
        f"Technique: {session.score_parts.get('technique', 0)}/20, "
        f"Protocol: {session.score_parts.get('protocol', 0)}/10"
    )

    context_text = (
        f"Session Scope: {session.session_id}\n"
        f"Experiment: {session.experiment_id}\n"
        f"Current Step: {step_title}\n"
        f"Spec Guidance: {step_hint}\n"
        f"PPE Worn: {ppe_str}\n"
        f"Score Breakdown: {score_str}\n"
        f"Recent Events: {events_str}\n"
        f"Violations: {violations_str}"
    )
    return context_text, step_title, step_hint


def build_spec_agent_context(session: LabSession) -> dict[str, Any]:
    """
    Build spec-driven agent context strictly for a single LabSession.
    """
    exp = get_experiment(session.experiment_id)
    step_idx = len(session.protocol_progress)
    current_step = exp.protocol[step_idx] if step_idx < len(exp.protocol) else None
    return {
        "session_id": session.session_id,
        "experiment_id": session.experiment_id,
        "ppe": sorted(session.ppe),
        "current_step": current_step,
        "completed_steps": list(session.protocol_progress),
        "violations": [v.rule_id for v in session.violations],
    }
