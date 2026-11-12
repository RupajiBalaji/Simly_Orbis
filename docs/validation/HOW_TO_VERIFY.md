# How to Verify Reference Data Rows

> **DISCLAIMER: Educational simulation platform. Not medical advice. Not clinical evidence.**
> Reference rows and validation metrics are educational benchmarks compared against published academic literature under specific laboratory conditions.

This guide outlines the protocol for the founder or authorized subject-matter expert to verify rows in the Simly Orbis validation datasets.

---

## 1. Verification Protocol

Only the founder or a qualified human expert may verify rows. Agents, automated scripts, and test runners must never modify the `verified_by` field from `"unverified"`.

1. **Open the Verification Worksheet**:
   - Inspect [docs/validation/VERIFICATION_WORKSHEET.md](VERIFICATION_WORKSHEET.md) or open [docs/validation/VERIFICATION_WORKSHEET.csv](VERIFICATION_WORKSHEET.csv) in a spreadsheet editor.
2. **Retrieve Primary Source**:
   - Locate the cited paper, official DOI, or textbook edition specified in the `source_citation` and `source_locator` columns.
3. **Confirm Values & Conditions**:
   - Verify that the reference value, unit, dose/regimen, and cohort conditions match the primary publication's text, tables, or figure legends.
   - Confirm standard unit conversions (e.g., $\mu\text{g/mL}$ to $\text{mg/L}$).
4. **Record Sign-off in Data File**:
   - Open the target CSV file in `validation/data/`:
     - `validation/data/chem_titration_references.csv`
     - `validation/data/pharma_pk_references.csv`
     - `validation/data/pharma_trial_references.csv`
   - Locate the verified row ID.
   - Replace `"unverified"` in the `verified_by` column with your verifier tag matching the format:
     `^[^:]+:\d{4}-\d{2}-\d{2}$`
     *(Example: `founder_jane:2026-11-20` or `dr_smith:2026-11-20`)*.
5. **Re-generate Worksheets and Validation Report**:
   ```bash
   # Re-generate expert verification worksheets
   python scripts/make_verification_worksheet.py

   # Re-run full validation report and plots
   python -c "import sys; sys.path.insert(0, 'backend'); from app.validation.runner import ValidationRunner; r = ValidationRunner(); r.run_and_save()"
   ```
6. **Verify Report Output**:
   - Verified rows will transition from "Pending Human Check" to "Human-Verified Validation Results".
   - The headline pass rate will reflect verified rows once verified count > 0.
