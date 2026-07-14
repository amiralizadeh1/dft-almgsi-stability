"""Convergence tables and diagnostics."""
from __future__ import annotations

import pandas as pd


def convergence_table(df: pd.DataFrame) -> pd.DataFrame:
    """Return valid convergence rows with successive eV/atom differences."""
    sub = df[(df["case_type"].str.contains("convergence", na=False)) & (df["valid_result"] == True)].copy()  # noqa: E712
    if sub.empty:
        return pd.DataFrame()
    sub = sub.sort_values(["case_type", "convergence_value" if "convergence_value" in sub else "case_id"])
    sub["energy_per_atom_ev"] = sub["total_energy_ev"] / sub["atom_count"]
    sub["delta_from_previous_ev_per_atom"] = sub.groupby("case_type")["energy_per_atom_ev"].diff()
    return sub
