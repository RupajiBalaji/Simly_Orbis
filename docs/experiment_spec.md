# Simly Orbis — Experiment Specification Guide

Authoring Interactive Virtual Science Laboratory Experiments Without Code.

---

## 1. Overview & Declarative Platform Architecture

Simly Orbis laboratory simulations are powered by a **declarative specification platform**. This enables educators, teachers, and instructional designers to design, balance, and publish interactive 3D laboratory experiments in standard **JSON** or **YAML** without modifying backend Python code or writing 3D graphics scripts.

### Core Architecture Principles
1. **Backend is the Single Source of Truth**: The simulation engine computes all physical chemistry, pharmacokinetics, and orbital mechanics outcomes. The 3D client purely executes visual directives emitted by the engine.
2. **AI Proposes, the Engine Decides**: Natural language student input is converted into structured action proposals by Ask Orbis, which are strictly validated against the experiment's allowlist and dry-run through the safety engine.
3. **Deterministic & Transparent**: Every rule check, score calculation, and visual directive is deterministic and traceable to the declarative specification.
4. **Pedagogical Safety**: Unsafe student actions are never artificially blocked; rather, the safety engine enforces real-time educational consequences and penalties.

---

## 2. Specification File Structure

An experiment specification file is placed in `specs/<experiment_id>.json` or `specs/<experiment_id>.yaml`. The schema strictly forbids unknown properties (`extra="forbid"`) to prevent silent configuration typos.

```
specs/
├── titration_bench.json
├── pk_ward.json
├── launch_bench.json
├── dose_lab.json
└── fixtures/
    └── worked_example_neutralization.json
```

### Top-Level Properties

| Field | Type | Description |
|---|---|---|
| `id` | `string` | Unique experiment slug (e.g. `worked_example_neutralization`). |
| `version` | `string` | Semantic version string (e.g. `1.0.0`). |
| `district` | `string` | One of `"chemistry"`, `"pharma"`, or `"space"`. |
| `title` | `string` | Plain-language human-readable experiment title. |
| `learning_goals`| `list[string]` | Bulleted list of curriculum learning objectives. |
| `difficulty` | `string` | One of `"beginner"`, `"intermediate"`, `"advanced"`, `"challenge"`. |
| `est_minutes` | `int` | Estimated completion duration in minutes (e.g. 15). |
| `engine` | `EngineSpec` | Engine identifier, minimum version, and parameter bounds. |
| `equipment` | `list[string]` | Apparatus identifiers present on the bench. |
| `steps` | `list[StepSpec]`| Ordered protocol steps required to complete the lab. |
| `rules` | `list[RuleSpec]`| Safety and laboratory protocol rules. |
| `scoring` | `ScoringSpec` | Categorical score weights and letter grade cutoffs. |
| `visual_directive_mapping` | `dict` | Mapping from simulation events to 3D client visuals. |
| `mentor` | `MentorSpec` | Hints per step and common mistake remedies. |
| `ask_orbis` | `AskOrbisSpec` | Natural language allowed actions and synonyms. |
| `model_card` | `string` | Relative path to documentation model card. |
| `provenance` | `ProvenanceBlock`| Author information and constant citations. |
| `i18n_keys` | `dict[str, str]` | Translation keys for all user-facing strings. |

---

## 3. Physical Engines & Parameter Bounds

Each experiment delegates numeric calculations to one of four verified backend calculation engines:

- `chem.titration`: Acid-base neutralization equilibrium calculations, Henderson-Hasselbalch buffer curves, pH endpoints, and volume tracking.
- `pharma.pk`: Deterministic one-compartment oral and IV pharmacokinetics, first-order absorption ($k_a$), elimination ($k_e$), and plasma concentration profiles.
- `pharma.trial`: Multi-patient virtual clinical trials and population pharmacokinetics.
- `space.orbit`: Two-body Keplerian mechanics, Tsiolkovsky rocket equation, ascent trajectories, and Hohmann orbital transfers.

### Specifying Parameter Bounds
Parameter bounds constrain user choices to realistic physical boundaries. Each bound includes `min`, `max`, `unit`, and `default`.

```json
"engine": {
  "id": "chem.titration",
  "minimum_version": "1.0.0",
  "parameter_bounds": {
    "analyte_volume_ml": {
      "min": 5.0,
      "max": 50.0,
      "unit": "mL",
      "default": 25.0
    },
    "titrant_volume_ml": {
      "min": 1.0,
      "max": 50.0,
      "unit": "mL",
      "default": 50.0
    },
    "analyte_concentration_m": {
      "min": 0.01,
      "max": 2.0,
      "unit": "M",
      "default": 0.1
    },
    "titrant_concentration_m": {
      "min": 0.01,
      "max": 2.0,
      "unit": "M",
      "default": 0.1
    }
  }
}
```

> [!IMPORTANT]
> The specification validator verifies that all declared parameter bounds fall strictly within certified physical limits of the underlying engine. Declaring bounds outside engine capability results in an immediate validation error.

---

## 4. Protocol Steps & Allowed Actions

Laboratory workflows proceed through a sequence of pedagogical steps. Each step defines the actions permitted during that phase, along with preconditions and state effects.

```json
"steps": [
  {
    "id": "wear_ppe",
    "title": "Wear Personal Protective Equipment (PPE)",
    "allowed_actions": ["wear_ppe"],
    "preconditions": [],
    "effects": ["ppe_worn"]
  },
  {
    "id": "rinse_burette",
    "title": "Rinse & Condition Burette",
    "allowed_actions": ["rinse_burette"],
    "preconditions": [],
    "effects": ["burette_rinsed"]
  }
]
```

---

## 5. Rules, Severity, & Conditionals

Safety and technique rules are evaluated whenever the student performs an action. Every rule must have:
- `id`: Rule identifier (e.g. `R1`, `R2`, `S1`, `D1`).
- `text`: Formal rule statement displayed in briefings and lab manuals.
- `severity`: `"info"`, `"penalty"`, `"block"`, or `"fail"`.
- `condition`: State condition flag evaluated by the engine.
- `hint`: Educational mentoring guidance explaining how to avoid or resolve the breach.

```json
{
  "id": "R1",
  "text": "Protective safety goggles must be equipped before handling active chemicals.",
  "severity": "penalty",
  "condition": "ppe_goggles_worn",
  "hint": "Put on safety goggles from the equipment tray before opening reagent bottles."
}
```

### Rule Severity Levels
1. **info**: Educational notification; zero score deduction.
2. **penalty**: Safety breach resulting in a scoring deduction (typically -10 to -20 points).
3. **block**: Action cannot proceed due to immediate physical hazard (e.g. pouring water directly into concentrated acid).
4. **fail**: Critical procedural failure resulting in experiment termination (e.g. fatal drug overdose or booster separation during motor burn).

---

## 6. Scoring Weights & Grade Thresholds

Scores in Simly Orbis are deterministic and broken down across four pedagogical dimensions totaling 100 points:

```json
"scoring": {
  "weights": {
    "safety": 40,
    "accuracy": 30,
    "technique": 20,
    "protocol": 10
  },
  "grade_thresholds": {
    "A": 90,
    "B": 80,
    "C": 70,
    "D": 60
  }
}
```

---

## 7. 3D Visual Directive Mapping

Visual directives instruct the 3D client how to render physical state transitions. The engine dictates what happens; the client merely displays the visual directive.

```json
"visual_directive_mapping": {
  "endpoint": {
    "type": "liquid",
    "hex": "#f472b6",
    "target": "conical_flask"
  },
  "splash": {
    "type": "effect",
    "name": "splash",
    "target": "sink"
  }
}
```

Allowed directive types:
- `liquid`: Renders liquid volume level and hex color tint.
- `flame`: Controls rocket engine or Bunsen burner exhaust flame.
- `effect`: Triggers particles (`splash`, `smoke`, `bubbles`, `steam`).
- `readout`: Renders floating digital HUD telemetry displays.

---

## 8. Dr. Orbis Mentoring & Common Mistakes

Dr. Orbis serves as an AI and rule-based lab instructor. The `mentor` block supplies hints for each protocol step and explicit remedies for common student misconceptions.

```json
"mentor": {
  "hints_per_step": {
    "wear_ppe": ["Put on all required safety gear: goggles, gloves, and lab coat."],
    "rinse_burette": ["Condition the burette by rinsing with a small portion (5 mL) of NaOH titrant."]
  },
  "common_mistakes": [
    {
      "id": "skipping_indicator",
      "trigger": "titrate before add_indicator",
      "remedy": "Always add 2-3 drops of indicator before dispensing titrant to observe equivalence color transition."
    }
  ]
}
```

---

## 9. Ask Orbis Natural Language Interface

Ask Orbis allows students to control the laboratory by speaking or typing natural language requests (e.g. *"zero the balance and add 2 drops indicator"*).

Teachers define the permitted action vocabulary and colloquial synonyms:

```json
"ask_orbis": {
  "allowed_actions": [
    "wear_ppe",
    "rinse_burette",
    "fill_burette",
    "pipette_analyte",
    "add_indicator",
    "titrate",
    "swirl",
    "record_endpoint",
    "dispose_waste",
    "wash_hands",
    "submit_report"
  ],
  "synonyms": {
    "wear_ppe": ["put on ppe", "don ppe", "wear safety gear"],
    "titrate": ["titrate", "dispense titrant", "drip naoh", "add titrant"],
    "swirl": ["swirl", "mix flask", "agitate flask"]
  }
}
```

---

## 10. Provenance, Scientific Constants, & Adult Boundaries

To ensure scientific integrity and eliminate hallucinations, physical constants must be accompanied by full provenance metadata.

```json
"provenance": {
  "author": "Simly Orbis Chemistry Curriculum Team",
  "model_card": "docs/model_cards/chem_titration_v1.md",
  "constants": {
    "kw_water": {
      "value": 1.0e-14,
      "unit": "mol^2/L^2",
      "source": "IUPAC standard at 25 deg C",
      "citation": "IUPAC Gold Book",
      "verified_by": "unverified",
      "retrieved_on": "",
      "notes": "Human verification required"
    }
  },
  "notes": "Educational neutralization experiment template for secondary chemistry classes."
}
```

> [!NOTE]
> Per Simly Orbis rule R3, `verified_by` must always be `"unverified"` and `retrieved_on` must remain empty until an accredited academic reviewer validates the entry. In pharmacology experiments, parameters are strictly restricted to adult reference ranges (age 18-90, weight 40-150 kg).

---

## 11. Internationalization (i18n)

Every user-facing label (titles, step descriptions) must map to an i18n translation key in `i18n_keys`. Hard-coded strings are rejected by the validator.

```json
"i18n_keys": {
  "title": "experiments.neutralization.title",
  "steps.wear_ppe.title": "experiments.neutralization.steps.wear_ppe.title",
  "steps.rinse_burette.title": "experiments.neutralization.steps.rinse_burette.title",
  "steps.fill_burette.title": "experiments.neutralization.steps.fill_burette.title",
  "steps.pipette_analyte.title": "experiments.neutralization.steps.pipette_analyte.title",
  "steps.add_indicator.title": "experiments.neutralization.steps.add_indicator.title",
  "steps.titrate.title": "experiments.neutralization.steps.titrate.title",
  "steps.swirl.title": "experiments.neutralization.steps.swirl.title",
  "steps.record_endpoint.title": "experiments.neutralization.steps.record_endpoint.title",
  "steps.dispose_waste.title": "experiments.neutralization.steps.dispose_waste.title",
  "steps.wash_hands.title": "experiments.neutralization.steps.wash_hands.title",
  "steps.submit_report.title": "experiments.neutralization.steps.submit_report.title"
}
```

---

## 12. Complete Worked Example: Vinegar Neutralization

The complete, certified worked example can be inspected directly at [worked_example_neutralization.json](file:///specs/fixtures/worked_example_neutralization.json).

You can validate this fixture or any new experiment file using the validation CLI:

```bash
# Validate all active specifications
python scripts/validate_specs.py

# Validate a specific new experiment or fixture
python scripts/validate_specs.py specs/fixtures/worked_example_neutralization.json
```

---

## 13. Rejection Rules Reference

The validation CLI enforces these strict rejection rules per Section 10 of the specification:
1. **Unknown fields**: Any property not declared in `ExperimentSpec` raises an error.
2. **Duplicate rule IDs**: Every rule ID within an experiment must be unique.
3. **Actions with no engine handler**: Every step and Ask Orbis action must map to a registered engine handler.
4. **Invalid directives**: Directives not matching the visual contract are rejected.
5. **Parameter bounds out of range**: Declared parameter bounds must not exceed the certified engine bounds.
6. **Constants without provenance**: Any constant missing source, verified_by, or citation is rejected.
7. **Hard-coded strings**: Missing i18n keys for steps or experiment title fail validation.
8. **Pharma adult boundaries**: Any pharma experiment specifying pediatric ages or weights fails validation.
