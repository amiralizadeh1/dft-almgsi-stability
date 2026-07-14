"""Matplotlib plotting helpers."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_convergence(df: pd.DataFrame, path: Path) -> Path:
    """Plot a convergence diagnostic without claiming convergence."""
    fig, ax = plt.subplots()
    x = df.get("convergence_value", df["case_id"])
    ax.plot(range(len(df)), df["energy_per_atom_ev"], marker="o")
    ax.set_xticks(range(len(df)), [str(v) for v in x], rotation=30, ha="right")
    ax.set_xlabel("Convergence setting")
    ax.set_ylabel("Energy per atom (eV/atom)")
    ax.set_title("Convergence diagnostic; no convergence assumed")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def plot_pair_binding(df: pd.DataFrame, path: Path) -> Path:
    """Plot pair-binding energy versus Mg-Si distance."""
    data = df.sort_values("distance_angstrom")
    fig, ax = plt.subplots()
    ax.plot(data["distance_angstrom"], data["binding_energy_ev"], marker="o")
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_xlabel("Mg-Si distance (Angstrom)")
    ax.set_ylabel("Pair-binding energy (eV)")
    ax.set_title("Positive binding energy means attraction")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path
