#!/usr/bin/env python3
"""
scripts/make_verification_worksheet.py
Generates expert human verification worksheets (Markdown and CSV)
for all 22 reference rows in Simly Orbis validation datasets.

Educational simulation platform. Not medical advice. Not clinical evidence.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

# Add backend directory to path to use ValidationRunner
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.validation.runner import ValidationRunner  # noqa: E402


def generate_worksheets() -> None:
    runner = ValidationRunner(
        data_dir=ROOT_DIR / "validation" / "data",
        tolerances_path=ROOT_DIR / "validation" / "tolerances.yaml",
    )
    evaluated = runner.evaluate_all()
    # All 22 items live in unverified_results (or verified_results if verified in future)
    # Using evaluated["unverified_results"] + evaluated["verified_results"] gives exact 1:1 reference rows
    all_results = evaluated.get("unverified_results", []) + evaluated.get("verified_results", [])
    if not all_results:
        all_results = evaluated.get("unverified_results", [])

    # Sort deterministically by id
    all_results.sort(key=lambda x: str(x.get("id", "")))

    out_docs = ROOT_DIR / "docs" / "validation"
    out_docs.mkdir(parents=True, exist_ok=True)
    csv_path = out_docs / "VERIFICATION_WORKSHEET.csv"
    md_path = out_docs / "VERIFICATION_WORKSHEET.md"

    columns = [
        "row_id",
        "drug_or_experiment",
        "quantity",
        "source_citation",
        "source_locator",
        "reference_value_and_unit",
        "model_value_and_unit",
        "fold_error_or_pct_error",
        "tolerance",
        "computed_status",
        "expert_confirms_value_YN",
        "expert_comment",
        "verified_by_name_date",
    ]

    rows_data: list[dict[str, str]] = []

    for item in all_results:
        row_id = str(item.get("id", ""))
        drug_exp = str(item.get("population_or_condition", "")) or str(item.get("dose_or_regimen", ""))
        quantity = str(item.get("quantity", ""))
        source_cit = str(item.get("source_citation", ""))
        source_loc = str(item.get("source_url_or_doi", ""))

        obs_val = item.get("observed", item.get("value", ""))
        unit = str(item.get("unit", ""))
        pred_val = item.get("predicted", item.get("predicted_value", ""))

        ref_str = f"{obs_val} {unit}".strip()
        mod_str = f"{round(pred_val, 4) if isinstance(pred_val, (int, float)) else pred_val} {unit}".strip()

        fold_err = item.get("fold_error")
        pct_err = item.get("pct_error")
        if fold_err is not None:
            err_str = f"{round(fold_err, 3)}x fold ({round(pct_err, 1)}%)" if pct_err is not None else f"{round(fold_err, 3)}x fold"
        else:
            err_str = f"{pct_err}%" if pct_err is not None else "N/A"

        tol_info = item.get("tolerance_applied", {})
        if isinstance(tol_info, dict):
            tol_str = f"Fold <= {tol_info.get('fold_tolerance', 2.0)}x"
        else:
            tol_str = "Fold <= 2.0x"

        comp_status = "PASS" if item.get("passed") else "FAIL"

        rows_data.append({
            "row_id": row_id,
            "drug_or_experiment": drug_exp,
            "quantity": quantity,
            "source_citation": source_cit,
            "source_locator": source_loc,
            "reference_value_and_unit": ref_str,
            "model_value_and_unit": mod_str,
            "fold_error_or_pct_error": err_str,
            "tolerance": tol_str,
            "computed_status": comp_status,
            "expert_confirms_value_YN": "",
            "expert_comment": "",
            "verified_by_name_date": "",
        })

    # 1. Write CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for r in rows_data:
            writer.writerow(r)

    # 2. Write Markdown Worksheet
    md_lines = [
        "# Expert Human Verification Worksheet",
        "",
        "> **DISCLAIMER: Educational simulation platform. Not medical advice. Not clinical evidence.**",
        "> Model predictions and simulation numbers are educational approximations and are currently **unverified**.",
        "> They do not constitute diagnostic standards, clinical evidence, or animal-replacement validation.",
        "",
        "## Instructions for the Human Expert Verifier",
        "",
        "Please review each of the 22 reference rows below against the stated primary literature source (full-text PDF, textbook, or official database):",
        "1. **Locate primary source**: Open the cited paper, DOI, or textbook chapter.",
        "2. **Confirm reference value & unit**: Confirm that the reference value and unit directly match the primary publication's table, figure, or text.",
        "3. **Check context/population**: Verify that the dose, regimen, analyte concentration, or patient cohort match the condition description.",
        "4. **Complete verification columns**:",
        "   - Record **Y** (confirmed) or **N** (discrepancy) in `Expert Confirms (Y/N)`.",
        "   - Add any relevant qualifying remarks in `Expert Comment`.",
        "   - If confirmed, record your name and date in the standard format `name:YYYY-MM-DD` (e.g. `dr_smith:2026-11-15`) in `verified_by (name:date)`.",
        "5. Once verified in this sheet, update the corresponding `verified_by` field in `validation/data/*.csv` per [HOW_TO_VERIFY.md](HOW_TO_VERIFY.md).",
        "",
        "---",
        "",
        f"**Total Reference Rows for Review**: {len(rows_data)}",
        "",
        "| Row ID | Drug / Experiment | Quantity | Citation | Source Locator | Reference Value | Model Value | Error | Tolerance | Status | Expert Confirms (Y/N) | Expert Comment | verified_by (name:date) |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: | :--- | :--- |",
    ]

    for r in rows_data:
        md_lines.append(
            f"| `{r['row_id']}` | {r['drug_or_experiment']} | `{r['quantity']}` | {r['source_citation']} | {r['source_locator']} | **{r['reference_value_and_unit']}** | {r['model_value_and_unit']} | {r['fold_error_or_pct_error']} | {r['tolerance']} | {r['computed_status']} |  |  |  |"
        )

    md_lines.append("")
    with open(md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(md_lines))

    print(f"[WORKSHEET] Generated {len(rows_data)} rows in:")
    print(f"  - {csv_path}")
    print(f"  - {md_path}")


if __name__ == "__main__":
    generate_worksheets()
