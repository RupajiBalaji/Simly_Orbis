# AI Evaluation Latest (`scripts/eval_ai.py`)

- **Timestamp (UTC):** 2026-11-28T13:47:36.370120+00:00
- **Mode:** Deterministic offline evaluation (`AI_ENABLED=False` rule-based/parser baseline + red-team refusal checks)

## Summary Results (First Run & After Fixes)

| Suite | Result | Notes |
| --- | --- | --- |
| Author suite | 8/8 | Core single/multi-action commands across experiments |
| Hard suite | 6/6 | Out-of-bounds, injection, and kinetics/buffer edge phrases |
| Red-team suite | 49/52 | Medical/dosing refusal across Ask Orbis and Dr. Orbis |
| Held-out suite (founder-written, not tuned) | NOT RUN, file missing | Reads `backend/tests/data/founder_heldout_phrases.json` if present |

## Notes
- Held-out suite is **founder-written, not tuned**. If `backend/tests/data/founder_heldout_phrases.json` is absent, this harness explicitly reports `NOT RUN, file missing`.
