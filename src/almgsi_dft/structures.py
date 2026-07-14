"""Deterministic ASE structure generation for Al-Mg-Si calculations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ase import Atoms
from ase.build import bulk

from .neighbour_shells import cell_vectors_list, select_shell_site

DEFAULT_AL_A = 4.05
DEFAULT_MG_A = 3.21
DEFAULT_MG_C = 5.21
DEFAULT_SI_A = 5.43
MG_INDEX = 0
SINGLE_SOLUTE_INDEX = 1


@dataclass(frozen=True)
class GeneratedStructure:
    """A structure and the metadata required to reproduce it."""

    atoms: Atoms
    metadata: dict[str, Any]


def primitive_fcc_al(a: float = DEFAULT_AL_A) -> Atoms:
    """Create primitive FCC Al."""
    return bulk("Al", "fcc", a=a, cubic=False)


def conventional_fcc_al(a: float = DEFAULT_AL_A) -> Atoms:
    """Create conventional cubic FCC Al."""
    return bulk("Al", "fcc", a=a, cubic=True)


def primitive_hcp_mg(a: float = DEFAULT_MG_A, c: float = DEFAULT_MG_C) -> Atoms:
    """Create primitive HCP Mg."""
    return bulk("Mg", "hcp", a=a, c=c)


def primitive_diamond_si(a: float = DEFAULT_SI_A) -> Atoms:
    """Create primitive diamond Si."""
    return bulk("Si", "diamond", a=a, cubic=False)


def al_2x2x2_conventional_supercell(a: float = DEFAULT_AL_A) -> Atoms:
    """Create a 32-site 2x2x2 conventional FCC Al supercell."""
    return conventional_fcc_al(a).repeat((2, 2, 2))


def composition_string(atoms: Atoms) -> str:
    """Return a stable chemical formula string."""
    return atoms.get_chemical_formula(mode="hill")


def _base_meta(case_id: str, atoms: Atoms, case_type: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "case_type": case_type,
        "composition": composition_string(atoms),
        "atom_count": len(atoms),
        "cell_vectors_angstrom": cell_vectors_list(atoms),
    }


def al32(a: float = DEFAULT_AL_A) -> GeneratedStructure:
    """Generate the pure Al32 defect reference supercell."""
    atoms = al_2x2x2_conventional_supercell(a)
    return GeneratedStructure(atoms, _base_meta("Al32", atoms, "defect") | {"required_symbols": ["Al"]})


def isolated_substitution(symbol: str, a: float = DEFAULT_AL_A) -> GeneratedStructure:
    """Generate Al31Mg or Al31Si with a deterministic substitution index."""
    atoms = al_2x2x2_conventional_supercell(a)
    atoms[SINGLE_SOLUTE_INDEX].symbol = symbol
    case_id = f"Al31{symbol}"
    return GeneratedStructure(
        atoms,
        _base_meta(case_id, atoms, "defect")
        | {"solute_symbol": symbol, "solute_index": SINGLE_SOLUTE_INDEX, "required_symbols": ["Al", symbol]},
    )


def mg_si_pair(shell: int | str, a: float = DEFAULT_AL_A, tolerance: float = 0.03) -> GeneratedStructure:
    """Generate a deterministic Mg-Si pair configuration by neighbour shell."""
    atoms = al_2x2x2_conventional_supercell(a)
    atoms[MG_INDEX].symbol = "Mg"
    site = select_shell_site(atoms, MG_INDEX, shell, tolerance)
    atoms[site.index].symbol = "Si"
    label = {1: "1NN", 2: "2NN", "far": "far"}[shell]
    case_id = f"Al30MgSi_{label}"
    return GeneratedStructure(
        atoms,
        _base_meta(case_id, atoms, "defect")
        | {
            "mg_index": MG_INDEX,
            "si_index": site.index,
            "neighbour_shell": site.shell,
            "initial_pair_distance_angstrom": site.distance,
            "shell_tolerance_angstrom": tolerance,
            "required_symbols": ["Al", "Mg", "Si"],
        },
    )


def elemental_reference_structures() -> dict[str, GeneratedStructure]:
    """Return elemental reference structures for vc-relax inputs."""
    structs = {
        "ref_Al_fcc": primitive_fcc_al(),
        "ref_Mg_hcp": primitive_hcp_mg(),
        "ref_Si_diamond": primitive_diamond_si(),
    }
    return {
        case_id: GeneratedStructure(
            atoms,
            _base_meta(case_id, atoms, "elemental_reference") | {"required_symbols": sorted(set(atoms.symbols))},
        )
        for case_id, atoms in structs.items()
    }


def default_defect_structures(al_lattice_constant: float, tolerance: float) -> dict[str, GeneratedStructure]:
    """Return all default 32-site fixed-cell defect structures."""
    structures = [
        al32(al_lattice_constant),
        isolated_substitution("Mg", al_lattice_constant),
        isolated_substitution("Si", al_lattice_constant),
        mg_si_pair(1, al_lattice_constant, tolerance),
        mg_si_pair(2, al_lattice_constant, tolerance),
        mg_si_pair("far", al_lattice_constant, tolerance),
    ]
    return {structure.metadata["case_id"]: structure for structure in structures}
