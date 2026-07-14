"""Energy formulas and compatibility checks."""
from __future__ import annotations

from typing import Any, Mapping

from .exceptions import IncompatibleCalculationError

RY_TO_EV = 13.605693122994


def ry_to_ev(value: float) -> float:
    """Convert Rydberg to eV."""
    return float(value) * RY_TO_EV


def ev_to_ry(value: float) -> float:
    """Convert eV to Rydberg."""
    return float(value) / RY_TO_EV


def chemical_potential(total_energy_ev: float, atom_count: int) -> float:
    """Return a bulk reference chemical potential in eV per atom."""
    if atom_count <= 0:
        raise ValueError("atom_count must be positive")
    return float(total_energy_ev) / atom_count


def substitution_formation_energy(
    defect_energy_ev: float, pure_energy_ev: float, mu_al_ev: float, mu_x_ev: float
) -> float:
    """Return E_f(X_Al) = E(Al_(N-1)X) - E(Al_N) + mu_Al - mu_X."""
    return float(defect_energy_ev) - float(pure_energy_ev) + float(mu_al_ev) - float(mu_x_ev)


def pair_binding_energy(e_mg_ev: float, e_si_ev: float, e_pair_ev: float, e_pure_ev: float) -> float:
    """Return Mg-Si pair binding energy, where positive means attraction."""
    return float(e_mg_ev) + float(e_si_ev) - float(e_pair_ev) - float(e_pure_ev)


COMPATIBILITY_KEYS = (
    "input_dft",
    "pseudopotential_identifiers",
    "ecutwfc_ry",
    "ecutrho_ry",
    "kpoints",
    "smearing",
    "degauss_ry",
    "supercell_dimensions",
    "atom_count",
    "relaxation_type",
)


def check_compatible(
    records: list[Mapping[str, Any]], keys: tuple[str, ...] = COMPATIBILITY_KEYS
) -> None:
    """Raise a clear error when energy records are incompatible."""
    if not records:
        raise IncompatibleCalculationError("No calculation records supplied")
    mismatches: list[str] = []
    for key in keys:
        if key not in records[0]:
            continue
        first = records[0].get(key)
        if any(record.get(key) != first for record in records[1:]):
            mismatches.append(key)
    if mismatches:
        raise IncompatibleCalculationError("Incompatible calculations for keys: " + ", ".join(mismatches))


def require_reference(records_by_case: Mapping[str, Mapping[str, Any]], case_id: str) -> Mapping[str, Any]:
    """Return a required reference record or raise a clear error."""
    try:
        return records_by_case[case_id]
    except KeyError as exc:
        raise KeyError(f"Required reference calculation missing: {case_id}") from exc
