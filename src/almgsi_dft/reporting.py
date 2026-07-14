"""Markdown report generation."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def generate_report(results_csv: Path, output: Path) -> Path:
    """Generate a Markdown results report without fabricating missing results."""
    df = pd.read_csv(results_csv) if results_csv.exists() else pd.DataFrame()
    invalid_count = 0 if df.empty else int((df["valid_result"] != True).sum())  # noqa: E712
    pseudos = _pseudo_summary(df)
    text = f"""# First-Principles Stability and Early Solute Clustering in Al-Mg-Si

## 1. Study objective
Calculate PBE Quantum ESPRESSO total energies for elemental Al, Mg and Si references and dilute Mg/Si solute configurations in a 32-site FCC Al supercell.

## 2. Computational method
Inputs are generated with ASE and run locally with `pw.x`. Energies are stored internally in eV. Failed or incomplete outputs are excluded from physical analysis.

## 3. Pseudopotentials used
{pseudos}

## 4. Convergence settings
Convergence evidence must come from explicit cut-off and k-point calculations. This report does not assume that any setting is converged.

## 5. Elemental reference structures
FCC Al, HCP Mg and diamond Si support `vc-relax`. Final elemental bulk energies per atom are zero-temperature DFT bulk reference chemical potentials, not finite-temperature thermodynamic chemical potentials.

## 6. Substitution formation energies
`E_f(X_Al) = E(Al_(N-1)X) - E(Al_N) + mu_Al - mu_X`.

## 7. Mg-Si pair-binding energies
`E_bind(r) = E(Al_(N-1)Mg) + E(Al_(N-1)Si) - E(Al_(N-2)MgSi; r) - E(Al_N)`.

## 8. Interpretation of positive and negative binding energies
Positive binding energy means attraction. Negative binding energy means the pair is less stable than isolated substitutions under the same convention.

## 9. Convergence evidence
Use the generated convergence CSV files and plots. The example 0.001 eV/atom threshold is a diagnostic, not a universal rule.

## 10. Excluded or failed calculations
{invalid_count} calculations were invalid, incomplete or failed and must not be used as scientific results.

## 11. Limitations
No DFT result is invented, estimated, interpolated or compared with experiment unless external validation is later supplied.

## 12. Relationship to precipitation and clustering models
The pair-binding trends can later inform early clustering, Monte Carlo or kinetic Monte Carlo models of Al-Mg-Si precipitation.

## 13. Possible future Monte Carlo or kinetic Monte Carlo extension
Future work could map validated DFT energies onto lattice interactions or kinetic event catalogues.

## 14. Possible future HPC extension
The workflow separates structure generation, inputs, parsing and analysis so an execution layer could be added later. No scheduler support is implemented here.

## 15. Reproduction commands
See `README.md` for installation, generation, execution, collection, analysis, reporting and archiving commands.
"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text)
    return output


def _pseudo_summary(df: pd.DataFrame) -> str:
    if df.empty or "pseudopotential_identifiers" not in df.columns:
        return "No pseudopotential metadata was available."
    values = sorted({str(v) for v in df["pseudopotential_identifiers"].dropna()})
    return "\n".join(f"- `{value}`" for value in values) if values else "No pseudopotential metadata was available."
