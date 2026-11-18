"""
Tests for Spec-Driven Mentor Hints, Ask Orbis Actions, and Synonyms (P2-T4).

Verifies:
1. Every rule ID across all experiment specifications has a non-empty educational hint.
2. Every synonym defined in ask_orbis.synonyms across all specs maps to a valid ActionType.
3. Allowed actions are dynamically sourced per experiment from spec.ask_orbis.allowed_actions.
4. Action synonyms are dynamically sourced per experiment from spec.ask_orbis.synonyms.
5. get_spec_mentor_hint correctly resolves rule hints, step hints, and common mistake remedies.
6. Dr. Orbis mentor explain and hint modes leverage spec-driven rule and step hints.
"""

from __future__ import annotations

from pathlib import Path
import pytest
from httpx import AsyncClient

from app.lab.agent import get_action_synonyms, get_allowed_actions
from app.lab.models import ActionType
from app.routes.tutor import (
    SimSummary,
    _template_response,
    get_spec_allowed_actions,
    get_spec_mentor_hint,
    get_spec_synonyms,
)
from app.specs.loader import get_spec_by_id, load_all_specs


SPECS_DIR = Path(__file__).resolve().parent.parent.parent / "specs"


def test_every_rule_id_has_a_hint():
    """Verify that every safety and protocol rule across all specs has an educational hint."""
    all_specs = load_all_specs(SPECS_DIR)
    assert len(all_specs) >= 4, f"Expected at least 4 specs, found {len(all_specs)}"

    total_rules = 0
    for exp_id, spec in all_specs.items():
        assert len(spec.rules) > 0, f"Spec {exp_id} has no rules defined"
        for rule in spec.rules:
            total_rules += 1
            hint = rule.hint or rule.text
            assert hint is not None and len(hint.strip()) > 0, (
                f"Rule '{rule.id}' in spec '{exp_id}' is missing a hint or text"
            )
            # Verify get_spec_mentor_hint resolves it
            resolved_hint = get_spec_mentor_hint(exp_id, rule_id=rule.id)
            assert resolved_hint is not None and len(resolved_hint.strip()) > 0, (
                f"Failed to resolve hint for rule '{rule.id}' in '{exp_id}'"
            )

    print(f"Verified hints for all {total_rules} rules across {len(all_specs)} experiment specs.")


def test_every_synonym_maps_to_valid_action_type():
    """Verify that every synonym key in ask_orbis.synonyms maps to a valid ActionType."""
    all_specs = load_all_specs(SPECS_DIR)
    valid_actions = {a.value for a in ActionType}

    total_synonym_phrases = 0
    for exp_id, spec in all_specs.items():
        synonyms = spec.ask_orbis.synonyms
        assert len(synonyms) > 0, f"Spec {exp_id} has no synonyms defined in ask_orbis"

        for action_key, phrases in synonyms.items():
            assert action_key in valid_actions, (
                f"Synonym key '{action_key}' in spec '{exp_id}' is not a valid ActionType. "
                f"Valid actions: {sorted(valid_actions)}"
            )
            assert isinstance(phrases, list) and len(phrases) > 0, (
                f"Synonym phrases for '{action_key}' in spec '{exp_id}' must be a non-empty list"
            )
            for phrase in phrases:
                total_synonym_phrases += 1
                assert isinstance(phrase, str) and len(phrase.strip()) > 0, (
                    f"Empty phrase under synonym key '{action_key}' in spec '{exp_id}'"
                )

    print(f"Verified {total_synonym_phrases} synonym phrases mapping to valid ActionTypes.")


def test_dynamic_allowed_actions_sourcing():
    """Verify get_allowed_actions retrieves experiment-specific allowlists."""
    titration_actions = get_allowed_actions("titration_bench")
    assert "titrate" in titration_actions
    assert "rinse_burette" in titration_actions
    assert "launch" not in titration_actions

    space_actions = get_allowed_actions("launch_bench")
    assert "launch" in space_actions
    assert "burn_transfer" in space_actions
    assert "titrate" not in space_actions

    dose_actions = get_allowed_actions("dose_lab")
    assert "run_simulation" in dose_actions
    assert "check_renal" in dose_actions
    assert "launch" not in dose_actions

    pk_actions = get_allowed_actions("pk_ward")
    assert "draw_blood" in pk_actions
    assert "run_assay" in pk_actions
    assert "burn_transfer" not in pk_actions


def test_dynamic_action_synonyms_sourcing():
    """Verify get_action_synonyms retrieves experiment-specific synonyms."""
    titration_syn = get_action_synonyms("titration_bench")
    assert "titrate" in titration_syn
    assert any("dispense naoh" in s or "titrate solution" in s for s in titration_syn["titrate"])

    space_syn = get_action_synonyms("launch_bench")
    assert "launch" in space_syn
    assert any("liftoff" in s for s in space_syn["launch"])

    dose_syn = get_action_synonyms("dose_lab")
    assert "run_simulation" in dose_syn
    assert any("simulate pkpd" in s for s in dose_syn["run_simulation"])


def test_spec_mentor_hint_resolution():
    """Verify get_spec_mentor_hint resolves step hints and rule hints."""
    # Step hint
    step_hint = get_spec_mentor_hint("titration_bench", step_id="rinse_burette")
    assert step_hint is not None
    assert "burette" in step_hint.lower()

    # Rule hint
    rule_hint = get_spec_mentor_hint("launch_bench", rule_id="S3")
    assert rule_hint is not None
    assert "twr" in rule_hint.lower() or "thrust" in rule_hint.lower()

    # Dose lab rule hint
    d2_hint = get_spec_mentor_hint("dose_lab", rule_id="D2")
    assert d2_hint is not None
    assert "renal" in d2_hint.lower()


def test_tutor_template_response_uses_spec_mentor_mistakes():
    """Verify _template_response leverages spec.mentor.common_mistakes remedies."""
    # Overdose scenario (toxic > 20%)
    toxic_summary = SimSummary(
        drug_name="Theophylline",
        dose_mg=1000.0,
        n_doses=3,
        interval_h=8.0,
        weight_kg=70.0,
        clearance_multiplier=1.0,
        peak_concentration=35.0,
        time_of_peak=2.0,
        pct_green=10.0,
        pct_red=60.0,
        score=25,
    )
    toxic_msg = _template_response(toxic_summary)
    assert "Try:" in toxic_msg or "reducing the dose" in toxic_msg
    assert "educational simulation" in toxic_msg.lower()

    # Underdose scenario (subtherapeutic < 30%)
    under_summary = SimSummary(
        drug_name="Gentamicin",
        dose_mg=20.0,
        n_doses=1,
        interval_h=24.0,
        weight_kg=70.0,
        clearance_multiplier=1.0,
        peak_concentration=1.5,
        time_of_peak=1.0,
        pct_green=15.0,
        pct_red=0.0,
        score=40,
    )
    under_msg = _template_response(under_summary)
    assert "Try:" in under_msg or "increasing the dose" in under_msg
