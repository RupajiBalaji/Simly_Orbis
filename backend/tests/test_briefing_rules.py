"""Tests for experiment-specific briefing rules in plain language (F4)."""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


EXPECTED_RULES = {
    "pk_ward": [f"R{i}" for i in range(1, 11)],
    "titration_bench": [f"R{i}" for i in range(1, 11)],
    "launch_bench": [f"S{i}" for i in range(1, 9)],
    "dose_lab": [f"D{i}" for i in range(1, 9)],
}

OTHER_RULE_PREFIXES = {
    "pk_ward": ("S", "D"),
    "titration_bench": ("S", "D"),
    "launch_bench": ("R", "D"),
    "dose_lab": ("R", "S"),
}


@pytest.mark.asyncio
async def test_experiment_briefing_rules_exact_match():
    """Verify each experiment briefing provides exactly its own rule IDs and no others."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for exp_id, expected_ids in EXPECTED_RULES.items():
            res = await ac.get(f"/api/lab/experiments/{exp_id}")
            assert res.status_code == 200, f"Failed fetching {exp_id}: {res.text}"
            data = res.json()

            assert "rules" in data, f"Experiment {exp_id} missing 'rules' field"
            rules = data["rules"]
            rule_ids = [r["rule_id"] for r in rules]

            # 1. Exactly the expected rule IDs in order
            assert rule_ids == expected_ids, (
                f"Experiment {exp_id} rule IDs mismatch. Expected {expected_ids}, got {rule_ids}"
            )

            # 2. Plain language checks: non-empty title and explanation
            for r in rules:
                assert r.get("title") and len(r["title"].strip()) > 3
                assert r.get("explanation") and len(r["explanation"].strip()) > 10

            # 3. Strictly NO rule IDs from other families
            other_prefixes = OTHER_RULE_PREFIXES[exp_id]
            for r_id in rule_ids:
                for bad_prefix in other_prefixes:
                    assert not r_id.startswith(bad_prefix), (
                        f"Experiment {exp_id} leaked foreign rule {r_id}!"
                    )


def test_briefing_rules_html_rendering_isolation():
    """Verify simulated briefing rules list contains only the experiment's own rules."""
    from backend.app.lab.experiments import get_experiment

    for exp_id, expected_ids in EXPECTED_RULES.items():
        exp = get_experiment(exp_id)
        rules = exp.rules

        # Simulate main.js rendering logic
        rendered_html = "".join([
            f'<li><strong>{r["rule_id"]}:</strong> <span>{r["title"]}</span> – <span>{r["explanation"]}</span></li>'
            for r in rules
        ])

        # Assert every expected rule ID is present
        for rid in expected_ids:
            assert f"<strong>{rid}:</strong>" in rendered_html

        # Assert foreign prefixes do not appear
        for bad_prefix in OTHER_RULE_PREFIXES[exp_id]:
            # For each number 1..10, confirm e.g. "S1:" or "D1:" is absent in pk_ward
            for num in range(1, 11):
                assert f"<strong>{bad_prefix}{num}:</strong>" not in rendered_html
