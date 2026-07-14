"""Quantum ESPRESSO output parsing with direct text integrity checks."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ase.io import read, write

from .energetics import ry_to_ev

ENERGY_RE = re.compile(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry")
NAT_RE = re.compile(r"number of atoms/cell\s*=\s*(\d+)")
ITER_RE = re.compile(r"convergence has been achieved\s+in\s+(\d+)\s+iterations", re.I)
WALL_RE = re.compile(r"PWSCF\s*:.*?([0-9.]+)s\s+WALL", re.I)
PRESS_RE = re.compile(r"P=\s*([-+0-9.Ee]+)")
FORCE_RE = re.compile(r"Total force\s*=\s*([-+0-9.Ee]+)")
FATAL_RE = re.compile(r"(Error in routine|%%%%%%%%%%%%|convergence NOT achieved|maximum number of steps|stopping)", re.I)


def parse_qe_output(path: str | Path) -> dict[str, Any]:
    """Parse a QE output file and reject incomplete or failed outputs."""
    p = Path(path)
    text = p.read_text(errors="replace") if p.exists() else ""
    energies = [float(value) for value in ENERGY_RE.findall(text)]
    atom_match = NAT_RE.search(text)
    iterations = ITER_RE.findall(text)
    forces = [float(value) for value in FORCE_RE.findall(text)]
    pressures = [float(value) for value in PRESS_RE.findall(text)]
    wall = WALL_RE.findall(text)
    job_done = "JOB DONE" in text
    scf_converged = "convergence has been achieved" in text
    ionic_converged = (
        "bfgs converged" in text.lower()
        or "end final coordinates" in text.lower()
        or "final scf calculation" in text.lower()
        or "Begin final coordinates" in text
    )
    fatal = FATAL_RE.search(text) is not None
    result: dict[str, Any] = {
        "output_path": str(p),
        "job_done": job_done,
        "scf_converged": scf_converged,
        "ionic_converged": ionic_converged,
        "fatal_error": fatal,
        "total_energy_ev": ry_to_ev(energies[-1]) if energies else None,
        "atom_count": int(atom_match.group(1)) if atom_match else None,
        "scf_iterations": int(iterations[-1]) if iterations else None,
        "wall_time_seconds": float(wall[-1]) if wall else None,
        "final_force_ry_bohr": forces[-1] if forces else None,
        "final_pressure_kbar": pressures[-1] if pressures else None,
    }
    result["valid_result"] = bool(job_done and scf_converged and not fatal and energies)
    return result


def export_relaxed_cif(output_path: str | Path, cif_path: str | Path) -> bool:
    """Export the final QE structure to CIF through ASE when possible."""
    try:
        atoms = read(str(output_path), format="espresso-out", index=-1)
    except Exception:
        return False
    write(str(cif_path), atoms)
    return True
