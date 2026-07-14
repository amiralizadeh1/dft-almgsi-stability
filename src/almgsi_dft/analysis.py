"""Scientific post-processing for valid QE results."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .energetics import chemical_potential, pair_binding_energy, substitution_formation_energy
from .plotting import plot_convergence, plot_pair_binding


def analyse_results(results_csv: Path, output_directory: Path) -> dict[str, Path]:
    """Analyse valid results, write processed tables and figures, and never infer missing data."""
    output_directory.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(results_csv)
    invalid = df[df["valid_result"] != True].copy()  # noqa: E712
    valid = df[df["valid_result"] == True].copy()  # noqa: E712
    outputs: dict[str, Path] = {}
    outputs["excluded"] = output_directory / "excluded_calculations.csv"
    invalid.to_csv(outputs["excluded"], index=False)
    refs = _elemental_refs(valid)
    ref_table = pd.DataFrame(refs).T.reset_index(names="element") if refs else pd.DataFrame()
    outputs["elemental_references"] = output_directory / "elemental_references.csv"
    ref_table.to_csv(outputs["elemental_references"], index=False)
    formations = _formation_energies(valid, refs)
    outputs["formation_energies"] = output_directory / "substitution_formation_energies.csv"
    formations.to_csv(outputs["formation_energies"], index=False)
    bindings = _pair_bindings(valid)
    outputs["pair_binding_energies"] = output_directory / "pair_binding_energies.csv"
    bindings.to_csv(outputs["pair_binding_energies"], index=False)
    if not bindings.empty:
        outputs["pair_binding_png"] = plot_pair_binding(bindings, output_directory / "pair_binding_vs_distance.png")
        plot_pair_binding(bindings, output_directory / "pair_binding_vs_distance.pdf")
    for case_type, name in [("convergence_cutoff", "cutoff_convergence"), ("convergence_kpoints", "kpoint_convergence")]:
        sub = valid[valid["case_type"] == case_type].copy()
        if not sub.empty:
            sub["energy_per_atom_ev"] = sub["total_energy_ev"] / sub["atom_count"]
            sub["delta_from_previous_ev_per_atom"] = sub["energy_per_atom_ev"].diff()
            outputs[name] = output_directory / f"{name}.csv"
            sub.to_csv(outputs[name], index=False)
            outputs[f"{name}_png"] = plot_convergence(sub, output_directory / f"{name}.png")
            plot_convergence(sub, output_directory / f"{name}.pdf")
    return outputs


def _elemental_refs(valid: pd.DataFrame) -> dict[str, dict[str, float]]:
    mapping = {"ref_Al_fcc": "Al", "ref_Mg_hcp": "Mg", "ref_Si_diamond": "Si"}
    refs: dict[str, dict[str, float]] = {}
    for case_id, symbol in mapping.items():
        row = valid[valid["case_id"] == case_id]
        if not row.empty:
            record = row.iloc[0]
            refs[symbol] = {
                "total_energy_ev": float(record.total_energy_ev),
                "atom_count": int(record.atom_count),
                "mu_ev_per_atom": chemical_potential(float(record.total_energy_ev), int(record.atom_count)),
            }
    return refs


def _formation_energies(valid: pd.DataFrame, refs: dict[str, dict[str, float]]) -> pd.DataFrame:
    rows = []
    pure = valid[valid["case_id"] == "Al32"]
    if pure.empty or "Al" not in refs:
        return pd.DataFrame(columns=["solute", "case_id", "formation_energy_ev", "sign_convention"])
    e_pure = float(pure.iloc[0].total_energy_ev)
    for solute, case_id in [("Mg", "Al31Mg"), ("Si", "Al31Si")]:
        defect = valid[valid["case_id"] == case_id]
        if not defect.empty and solute in refs:
            rows.append(
                {
                    "solute": solute,
                    "case_id": case_id,
                    "formation_energy_ev": substitution_formation_energy(
                        float(defect.iloc[0].total_energy_ev),
                        e_pure,
                        refs["Al"]["mu_ev_per_atom"],
                        refs[solute]["mu_ev_per_atom"],
                    ),
                    "sign_convention": "E(defect)-E(Al_N)+mu_Al-mu_X",
                }
            )
    return pd.DataFrame(rows)


def _pair_bindings(valid: pd.DataFrame) -> pd.DataFrame:
    pure = valid[valid["case_id"] == "Al32"]
    mg = valid[valid["case_id"] == "Al31Mg"]
    si = valid[valid["case_id"] == "Al31Si"]
    if pure.empty or mg.empty or si.empty:
        return pd.DataFrame(columns=["case_id", "distance_angstrom", "binding_energy_ev"])
    rows = []
    for _, row in valid[valid["case_id"].str.startswith("Al30MgSi_")].iterrows():
        rows.append(
            {
                "case_id": row.case_id,
                "neighbour_shell": row.neighbour_shell,
                "distance_angstrom": row.final_pair_distance_angstrom
                if pd.notna(row.final_pair_distance_angstrom)
                else row.initial_pair_distance_angstrom,
                "binding_energy_ev": pair_binding_energy(
                    float(mg.iloc[0].total_energy_ev),
                    float(si.iloc[0].total_energy_ev),
                    float(row.total_energy_ev),
                    float(pure.iloc[0].total_energy_ev),
                ),
                "sign_convention": "positive means attraction",
            }
        )
    return pd.DataFrame(rows)
