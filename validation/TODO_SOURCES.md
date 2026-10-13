# Validation Literature Tracking: TODO Sources

This file records references and datasets flagged for future retrieval, physical library inspection, or paywall extraction.
Per validation rules: **no data may be added without verified provenance.** If a full-text cannot be accessed, it is listed here rather than included in the CSV files.

---

## 1. Pharmacokinetics & Population Dynamics (Pharma District)

1. **Aspirin / Salicylate Single-Dose Pharmacokinetics**
   - **Target Parameters**: Oral absorption $k_a$, volume of distribution $V_d$, non-linear Michaelis-Menten elimination constants ($V_{max}, K_m$).
   - **Potential Source**: Levy G. Clinical pharmacokinetics of aspirin. *Pediatrics*. 1978;62(5 Pt 2):867-872.
   - **Reason Pending**: Non-linear saturation kinetics required for aspirin are outside the scope of current one-compartment linear Bateman model; full-text curves require extraction with digitization software.

2. **Theophylline Sustained-Release Formulations**
   - **Target Parameters**: Extended zero-order absorption rate and steady-state fluctuation index.
   - **Potential Source**: Hendeles L, Weinberger M. Theophylline: a "state of the art" review. *Pharmacotherapy*. 1983;3(1):2-44.
   - **Reason Pending**: Sustained-release zero-order absorption not yet implemented in `pharma.pk`.

3. **Renal Failure / Dialysis Clearance Cohort**
   - **Target Parameters**: Fraction excreted unchanged $f_e$ and clearance reduction in severe renal impairment (eGFR < 15 mL/min).
   - **Potential Source**: Verbeeck RK, Musuamba FT. Pharmacokinetics and dosage adjustment in patients with renal impairment. *Eur J Clin Pharmacol*. 2009;65(8):757-773.
   - **Reason Pending**: Requires renal impairment subgroup module alongside current hepatic impairment subgroup.

4. **Pediatric Paracetamol Trial Population Variance**
   - **Target Parameters**: Weight-stratified pediatric trial inter-individual variance band.
   - **Potential Source**: Anderson BJ et al. Pediatric pharmacokinetics of paracetamol. *Paediatr Anaesth*. 1999;9(4):301-309. doi:10.1046/j.1460-9592.1999.00358.x
   - **Reason Pending**: Extracted raw individual curves required for exact 5th-95th percentile comparison.

---

## 2. Acid-Base Equilibrium & Analytical Chemistry (Chemistry District)

1. **Polyprotic Phosphoric Acid ($H_3PO_4$) Titration Curve**
   - **Target Parameters**: Sequential dissociation constants $pK_{a1} = 2.148$, $pK_{a2} = 7.198$, $pK_{a3} = 12.375$.
   - **Potential Source**: Goldberg RN, Kishore N, Lennen RM. Thermodynamic quantities for the ionization reactions of buffers in water. *J Phys Chem Ref Data*. 2002;31(2):231-370.
   - **Reason Pending**: Engine currently models monoprotic strong and weak acids; triprotic charge-balance cubic solver required.

2. **Carbonate Buffer System Under Atmospheric Carbon Dioxide ($CO_2$) Equilibrium**
   - **Target Parameters**: Henry's law constant $K_H$, open-system carbonic acid buffer capacity.
   - **Potential Source**: Butler JN. *Ionic Equilibrium: Solubility and pH Calculations*. Wiley-Interscience; 1998.
   - **Reason Pending**: Closed-vessel assumption currently active; open atmospheric $CO_2$ mass transfer not modeled.

---

## 3. Human Verification Protocol for Pending Rows

Rows marked with `verified_by = "unverified"` in `validation/data/*.csv`:
1. Obtain official DOI or physical textbook copy.
2. Cross-verify reported tabular numbers with text and figure captions.
3. Check units and conversions (e.g., $\mu\text{g/mL}$ to $\text{mg/L}$).
4. Change column value from `unverified` to verifier's signature (e.g. `human_verified`).
5. Re-run validation runner: `python -m backend.app.validation.runner`.
