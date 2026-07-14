"""Argparse command-line interface."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
from ase.io import read

from .analysis import analyse_results
from .config import load_config, validate_config
from .parser import parse_qe_output
from .qe_inputs import generate_run
from .reporting import generate_report
from .runner import run_case, run_case_list


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(prog="almgsi-dft")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("validate-config")
    p.add_argument("--config", required=True)
    p = sub.add_parser("generate")
    p.add_argument("--config", required=True)
    p.add_argument("--output", required=True)
    p = sub.add_parser("list-cases")
    p.add_argument("--run-directory", required=True)
    p = sub.add_parser("run-local")
    p.add_argument("--run-directory", required=True)
    p.add_argument("--case", required=True)
    p.add_argument("--nprocs", type=int, required=True)
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("run-set")
    p.add_argument("--run-directory", required=True)
    p.add_argument("--case-list", required=True)
    p.add_argument("--nprocs", type=int, required=True)
    p.add_argument("--failure-limit", type=int, default=1)
    p = sub.add_parser("status")
    p.add_argument("--run-directory", required=True)
    p = sub.add_parser("collect")
    p.add_argument("--run-directory", required=True)
    p.add_argument("--output", required=True)
    p = sub.add_parser("analyse")
    p.add_argument("--results", required=True)
    p.add_argument("--output-directory", required=True)
    p = sub.add_parser("report")
    p.add_argument("--results", required=True)
    p.add_argument("--output", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate-config":
            cfg = load_config(args.config)
            for warning in validate_config(cfg):
                print(f"WARNING: {warning}")
            print("Configuration is valid.")
        elif args.command == "generate":
            cfg = load_config(args.config)
            generated = generate_run(cfg, Path(args.output))
            print(f"Generated {len(generated)} case directories in {args.output}")
        elif args.command == "list-cases":
            for path in sorted(Path(args.run_directory).glob("*/metadata.json")):
                print(path.parent.name)
        elif args.command == "run-local":
            run_case(_config_from_run_directory(Path(args.run_directory)), Path(args.run_directory), args.case, args.nprocs, force=args.force)
        elif args.command == "run-set":
            return run_case_list(
                _config_from_run_directory(Path(args.run_directory)),
                Path(args.run_directory),
                Path(args.case_list),
                args.nprocs,
                args.failure_limit,
            )
        elif args.command == "status":
            for row in _status_rows(Path(args.run_directory)):
                print(f"{row['case_id']}: {row.get('status')} valid={row.get('valid_result')}")
        elif args.command == "collect":
            collect_results(Path(args.run_directory), Path(args.output))
        elif args.command == "analyse":
            analyse_results(Path(args.results), Path(args.output_directory))
        elif args.command == "report":
            generate_report(Path(args.results), Path(args.output))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


def _config_from_run_directory(run_directory: Path):
    config_path = run_directory / "config.yaml"
    if config_path.exists():
        return load_config(config_path)
    raise FileNotFoundError("Run directory is missing config.yaml; generated runs keep their config beside cases")


def _status_rows(run_directory: Path) -> list[dict]:
    return [json.loads(path.read_text()) for path in sorted(run_directory.glob("*/run_status.json"))]


def collect_results(run_directory: Path, output: Path) -> Path:
    """Collect one CSV row per case, retaining invalid and incomplete outputs."""
    rows = []
    for meta_path in sorted(run_directory.glob("*/metadata.json")):
        case_dir = meta_path.parent
        meta = json.loads(meta_path.read_text())
        status_path = case_dir / "run_status.json"
        status = json.loads(status_path.read_text()) if status_path.exists() else {}
        if (case_dir / "pw.out").exists():
            status |= parse_qe_output(case_dir / "pw.out")
        settings = meta.get("calculation_settings", {})
        total = status.get("total_energy_ev")
        atom_count = status.get("atom_count") or meta.get("atom_count")
        final_pair_distance = status.get("final_pair_distance_angstrom") or _final_pair_distance(case_dir, meta)
        rows.append(
            {
                "case_id": meta.get("case_id"),
                "case_type": meta.get("case_type"),
                "composition": meta.get("composition"),
                "calculation_type": meta.get("calculation_type"),
                "atom_count": atom_count,
                "neighbour_shell": meta.get("neighbour_shell"),
                "initial_pair_distance_angstrom": meta.get("initial_pair_distance_angstrom"),
                "final_pair_distance_angstrom": final_pair_distance,
                "total_energy_ev": total,
                "energy_per_atom_ev": total / atom_count if total is not None and atom_count else None,
                "scf_converged": status.get("scf_converged", False),
                "ionic_converged": status.get("ionic_converged", False),
                "job_done": status.get("job_done", False),
                "valid_result": status.get("valid_result", False),
                "ecutwfc_ry": settings.get("ecutwfc"),
                "ecutrho_ry": settings.get("ecutrho"),
                "kpoints": settings.get("kpoints"),
                "smearing": settings.get("smearing"),
                "degauss_ry": settings.get("degauss"),
                "pseudopotential_identifiers": meta.get("pseudopotential_identifiers"),
                "wall_time_seconds": status.get("wall_time_seconds"),
                "output_path": str(case_dir / "pw.out"),
            }
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output, index=False)
    print(f"Wrote {output}")
    return output


def _final_pair_distance(case_dir: Path, metadata: dict) -> float | None:
    cif = case_dir / "structure_final.cif"
    if not cif.exists() or "mg_index" not in metadata or "si_index" not in metadata:
        return None
    try:
        atoms = read(cif)
        return float(atoms.get_distance(int(metadata["mg_index"]), int(metadata["si_index"]), mic=True))
    except Exception:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
