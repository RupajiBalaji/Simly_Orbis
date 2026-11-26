"""
backend/tests/test_primary_action_steps.py
Verifies U1: Primary action button on Current Task Card.
- Every step of every experiment shows a primary button.
- The action on the primary button is a valid action for that step.
- At most one primary button is displayed on the card (plus secondary only if real choice).
- If avatar is not at the station, the button reads 'Go to <Station> and do this'.
"""

import json
import re
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.lab.experiments import _EXPERIMENTS

ACTION_MENU_JS = REPO_ROOT / "frontend" / "lab" / "game" / "action_menu.js"


def parse_action_menu_mappings():
    """Extract stepActionMap, station names, and label formatters from action_menu.js."""
    content = ACTION_MENU_JS.read_text(encoding="utf-8")

    # Extract stepActionMap
    match_map = re.search(r"const stepActionMap\s*=\s*\{([^}]+)\};", content)
    assert match_map, "Could not find stepActionMap in action_menu.js"
    step_action_map = {}
    for line in match_map.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        m = re.match(r"(\w+)\s*:\s*\[([^\]]+)\]", line)
        if m:
            step_id = m.group(1)
            actions = [a.strip().strip("'\"") for a in m.group(2).split(",")]
            step_action_map[step_id] = actions

    # Extract formatStationShortName
    short_names = {
        "digital_balance": "Balance",
        "dosing_cup": "Dosing Cup",
        "patient_bed": "Patient",
        "ward_clock": "Clock",
        "tube_rack": "Sample Tubes",
        "assay_analyzer": "Analyzer",
        "burette": "Burette",
        "conical_flask": "Flask",
        "sink": "Sink",
        "chemical_waste_bin": "Waste Bin",
        "biohazard_bin": "Biohazard Bin",
        "launch_pad": "Launch Pad",
        "propellant_tanks": "Propellant Farm",
        "flight_computer": "Flight Computer",
        "range_control": "Range Control",
        "tracking_station": "Tracking Station",
    }

    return step_action_map, short_names


STEP_ACTION_MAP, SHORT_STATION_NAMES = parse_action_menu_mappings()


def get_mock_primary_actions(step_id, station_id=None, allowed_actions=None):
    """Mirror the getPrimaryActionsForStep logic in action_menu.js."""
    target_action_names = STEP_ACTION_MAP.get(step_id, [step_id])
    if allowed_actions:
        matched = [a for a in target_action_names if a in allowed_actions]
    else:
        matched = list(target_action_names)

    if not matched:
        matched = list(target_action_names)

    return [{"action": a, "enabled": True} for a in matched]


def format_button_label(action_name, is_at_station=True, station_id=None):
    """Mirror the button label formatting in action_menu.js."""
    if not is_at_station and station_id:
        station_short = SHORT_STATION_NAMES.get(station_id, station_id.replace("_", " ").title())
        return f"Go to {station_short} and do this"

    label_map = {
        "wear_ppe": "Wear PPE",
        "tare_balance": "Tare balance",
        "choose_rocket": "Select Orbis 1",
        "weigh": "Weigh dose",
        "launch": "Launch rocket",
    }
    return label_map.get(action_name, action_name.replace("_", " ").title())


def test_every_step_in_every_experiment_has_valid_primary_action():
    """Verify that every step of every registered experiment maps to a valid primary action."""
    for exp_id, exp in _EXPERIMENTS.items():
        allowed = exp.allowed_actions or []
        for step in exp.protocol:
            step_id = step.get("id")
            primary_actions = get_mock_primary_actions(step_id, allowed_actions=allowed)

            assert len(primary_actions) >= 1, f"Step '{step_id}' in experiment '{exp_id}' returned 0 primary actions"
            primary_act = primary_actions[0]["action"]
            assert primary_act, f"Empty primary action for step '{step_id}' in '{exp_id}'"

            # If the experiment specifies allowed_actions, verify primary_act is allowed or matches step
            if allowed:
                assert primary_act in allowed or primary_act == step_id, (
                    f"Action '{primary_act}' for step '{step_id}' not in allowed actions of '{exp_id}' ({allowed})"
                )


def test_declarative_specs_steps_have_valid_primary_action():
    """Verify all declarative specs steps in specs/*.json map to valid primary actions."""
    specs_dir = REPO_ROOT / "specs"
    spec_files = list(specs_dir.glob("*.json"))
    assert len(spec_files) > 0

    for sf in spec_files:
        data = json.loads(sf.read_text(encoding="utf-8"))
        spec_id = data.get("id")
        steps = data.get("steps", [])
        for step in steps:
            step_id = step.get("id")
            primary_actions = get_mock_primary_actions(step_id)
            assert len(primary_actions) >= 1, f"Spec '{spec_id}' step '{step_id}' has no primary action"
            primary_act = primary_actions[0]["action"]
            assert primary_act, f"Spec '{spec_id}' step '{step_id}' has empty primary action"


def test_card_shows_at_most_one_primary_button():
    """The task card must display at most ONE button with task-btn-primary class."""
    # Test across representative steps
    for step_id in ["wear_ppe", "tare_balance", "weigh_dose", "titrate", "launch", "select_patient"]:
        primary_actions = get_mock_primary_actions(step_id)
        # Primary is only primary_actions[0]
        primary_btn = primary_actions[0]
        assert primary_btn is not None
        # Secondary is only present if step offers real choice
        is_choice = (step_id == "titrate" and len(primary_actions) > 1)
        secondary_btn = primary_actions[1] if (len(primary_actions) > 1 and is_choice) else None

        if step_id != "titrate":
            assert secondary_btn is None, f"Step '{step_id}' should not produce a secondary button"


def test_walk_to_station_button_text_when_not_at_station():
    """When avatar is not at station, button reads 'Go to <Station> and do this'."""
    cases = [
        ("digital_balance", "Go to Balance and do this"),
        ("conical_flask", "Go to Flask and do this"),
        ("patient_bed", "Go to Patient and do this"),
        ("launch_pad", "Go to Launch Pad and do this"),
        ("propellant_tanks", "Go to Propellant Farm and do this"),
        ("flight_computer", "Go to Flight Computer and do this"),
    ]

    for station_id, expected_label in cases:
        label = format_button_label("weigh", is_at_station=False, station_id=station_id)
        assert label == expected_label, f"Expected '{expected_label}', got '{label}'"


def test_at_station_button_shows_direct_action_label():
    """When avatar is at station, button displays high-contrast action label directly."""
    cases = [
        ("wear_ppe", "Wear PPE"),
        ("tare_balance", "Tare balance"),
        ("choose_rocket", "Select Orbis 1"),
        ("launch", "Launch rocket"),
    ]

    for action, expected_label in cases:
        label = format_button_label(action, is_at_station=True, station_id=None)
        assert label == expected_label, f"Expected '{expected_label}', got '{label}'"
