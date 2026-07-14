"""Quantum ESPRESSO input generation using ASE."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ase import Atoms
from ase.io import write
from ase.io.espresso import write_espresso_in

from .config import WorkflowConfig, validate_config
from .structures import (
    GeneratedStructure,
    default_defect_structures,
    elemental_reference_structures,
    primitive_fcc_al,
)


def case_settings(config: WorkflowConfig, metadata: dict[str, Any]) -> dict[str, Any]:
    """Return QE settings for a case."""
    settings = config.settings
    occupations = settings.get("occupations", "smearing")
    if set(metadata.get("required_symbols", [])) == {"Si"} and settings.get("si_occupations"):
        occupations = settings["si_occupations"]
    return {
        "calculation": metadata.get("calculation_type", "scf"),
        "ecutwfc": settings.get("ecutwfc_ry", 20),
        "ecutrho": settings.get("ecutrho_ry", 160),
        "kpoints": tuple(settings.get("kpoints", [2, 2, 2])),
        "occupations": occupations,
        "smearing": settings.get("smearing", "mv"),
        "degauss": settings.get("degauss_ry", 0.02),
        "conv_thr": settings.get("conv_thr", 1e-8),
        "forc_conv_thr": settings.get("forc_conv_thr", 1e-4),
        "press_conv_thr": settings.get("press_conv_thr", 0.5),
        "electron_maxstep": settings.get("electron_maxstep", 100),
        "nstep": settings.get("nstep"),
        "disk_io": settings.get("disk_io", "low"),
        "tstress": bool(settings.get("tstress", True)),
        "tprnfor": bool(settings.get("tprnfor", True)),
    }


def write_pw_input(path: Path, atoms: Atoms, config: WorkflowConfig, metadata: dict[str, Any]) -> None:
    """Write a QE `pw.x` input file through ASE."""
    settings = case_settings(config, metadata)
    pseudo_map = {s: f for s, f in config.pseudo_files().items() if s in set(atoms.symbols)}
    pseudo_dir = _pseudo_dir_for_case(path.parent, config)
    input_data: dict[str, Any] = {
        "control": {
            "calculation": settings["calculation"],
            "prefix": metadata["case_id"].replace("-", "_"),
            "pseudo_dir": pseudo_dir,
            "outdir": "qe_tmp",
            "tstress": settings["tstress"],
            "tprnfor": settings["tprnfor"],
            "disk_io": settings["disk_io"],
        },
        "system": {
            "input_dft": "PBE",
            "ecutwfc": settings["ecutwfc"],
            "ecutrho": settings["ecutrho"],
            "occupations": settings["occupations"],
            "smearing": settings["smearing"],
            "degauss": settings["degauss"],
        },
        "electrons": {
            "conv_thr": settings["conv_thr"],
            "electron_maxstep": settings["electron_maxstep"],
        },
        "ions": {"ion_dynamics": "bfgs"},
        "cell": {"press_conv_thr": settings["press_conv_thr"]},
    }
    if settings["nstep"] is not None:
        input_data["control"]["nstep"] = settings["nstep"]
    if settings["occupations"] == "fixed":
        input_data["system"].pop("smearing", None)
        input_data["system"].pop("degauss", None)
    with path.open("w") as handle:
        write_espresso_in(
            handle,
            atoms,
            input_data=input_data,
            pseudopotentials=pseudo_map,
            kpts=settings["kpoints"],
        )


def _pseudo_dir_for_case(case_dir: Path, config: WorkflowConfig) -> str:
    """Return a case-local pseudo_dir without embedding machine-specific paths."""
    configured = config.pseudopotentials.get("pseudo_dir") or config.settings.get("pseudo_dir") or "pseudos"
    configured_path = Path(configured)
    if configured_path.is_absolute():
        return str(configured_path).replace("\\", "/")
    project_root = _project_root_from_config(config)
    absolute_pseudo_dir = config.pseudo_dir(project_root)
    return os.path.relpath(absolute_pseudo_dir, start=case_dir).replace("\\", "/")


def _project_root_from_config(config: WorkflowConfig) -> Path:
    """Infer the project root from a checked-in config path."""
    config_path = config.path.resolve()
    if config_path.parent.name == "config":
        return config_path.parent.parent
    return Path.cwd().resolve()


def write_case(run_dir: Path, config: WorkflowConfig, structure: GeneratedStructure) -> Path:
    """Write `pw.in`, initial CIF, metadata and generated status for one case."""
    case_id = structure.metadata["case_id"]
    case_dir = run_dir / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    metadata = dict(structure.metadata)
    metadata.setdefault("calculation_type", "scf")
    metadata["calculation_settings"] = case_settings(config, metadata)
    metadata["pseudopotential_identifiers"] = config.pseudo_files()
    write(case_dir / "structure_initial.cif", structure.atoms)
    (case_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    (case_dir / "run_status.json").write_text(json.dumps({"case_id": case_id, "status": "generated"}, indent=2))
    write_pw_input(case_dir / "pw.in", structure.atoms, config, metadata)
    return case_dir


def generate_run(config: WorkflowConfig, output: Path) -> list[Path]:
    """Generate all requested case directories without executing calculations."""
    warnings = validate_config(config, require_pseudos_exist=False)
    output.mkdir(parents=True, exist_ok=True)
    (output / "config.yaml").write_text(config.path.read_text())
    generated: list[Path] = []
    if config.profile == "local_smoke" or config.cases.get("smoke"):
        generated.append(
            write_case(
                output,
                config,
                GeneratedStructure(
                    primitive_fcc_al(),
                    {
                        "case_id": "smoke_al_fcc_primitive_scf",
                        "case_type": "smoke",
                        "composition": "Al",
                        "atom_count": 1,
                        "calculation_type": "scf",
                        "scientific_warning": "Scientifically unconverged smoke-test settings.",
                        "required_symbols": ["Al"],
                    },
                ),
            )
        )
    if config.cases.get("include_elemental_refs"):
        for structure in elemental_reference_structures().values():
            structure.metadata["calculation_type"] = "vc-relax"
            generated.append(write_case(output, config, structure))
    if config.cases.get("include_defects"):
        tol = float(config.settings.get("shell_tolerance_angstrom", 0.03))
        a = float(config.settings.get("al_lattice_constant_angstrom", 4.05))
        for structure in default_defect_structures(a, tol).values():
            structure.metadata["calculation_type"] = "relax"
            structure.metadata["fixed_cell_uses_optimised_al_lattice"] = True
            generated.append(write_case(output, config, structure))
    if config.cases.get("include_convergence"):
        generated.extend(generate_convergence_cases(config, output))
    if warnings:
        (output / "WARNINGS.txt").write_text("\n".join(warnings) + "\n")
    return generated


def generate_convergence_cases(config: WorkflowConfig, output: Path) -> list[Path]:
    """Generate Al cut-off and k-point convergence inputs."""
    conv = config.raw.get("convergence", {})
    atoms = primitive_fcc_al()
    generated: list[Path] = []
    for ecut in conv.get("cutoff_values_ry", []):
        raw = dict(config.raw)
        raw["settings"] = dict(config.settings) | {
            "ecutwfc_ry": ecut,
            "ecutrho_ry": 8 * ecut,
            "kpoints": conv.get("cutoff_fixed_kpoints", [8, 8, 8]),
        }
        local = WorkflowConfig(config.path, raw)
        meta = {
            "case_id": f"conv_cutoff_al_ecut{ecut}",
            "case_type": "convergence_cutoff",
            "composition": "Al",
            "atom_count": 1,
            "calculation_type": "scf",
            "convergence_parameter": "ecutwfc_ry",
            "convergence_value": ecut,
            "required_symbols": ["Al"],
        }
        generated.append(write_case(output, local, GeneratedStructure(atoms, meta)))
    for grid in conv.get("kpoint_grids", []):
        label = "x".join(str(x) for x in grid)
        raw = dict(config.raw)
        raw["settings"] = dict(config.settings) | {
            "ecutwfc_ry": conv.get("kpoint_fixed_ecutwfc_ry"),
            "ecutrho_ry": conv.get("kpoint_fixed_ecutrho_ry"),
            "kpoints": grid,
        }
        local = WorkflowConfig(config.path, raw)
        meta = {
            "case_id": f"conv_kpoints_al_{label}",
            "case_type": "convergence_kpoints",
            "composition": "Al",
            "atom_count": 1,
            "calculation_type": "scf",
            "convergence_parameter": "kpoints",
            "convergence_value": label,
            "required_symbols": ["Al"],
        }
        generated.append(write_case(output, local, GeneratedStructure(atoms, meta)))
    return generated
