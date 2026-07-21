"""Local, foreground-only Quantum ESPRESSO execution."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from .config import WorkflowConfig, ensure_pseudopotentials, required_symbols
from .exceptions import RunError
from .parser import export_relaxed_cif, parse_qe_output


def resolve_qe_command(config: WorkflowConfig, nprocs: int) -> list[str]:
    """Resolve the QE command from environment, YAML or `pw.x` default."""
    command = os.environ.get("QE_PW_COMMAND") or config.settings.get("qe_command") or "pw.x"
    parts = shlex.split(str(command))
    if parts == ["pw.x"] and nprocs > 1:
        return ["mpirun", "-np", str(nprocs), "pw.x"]
    return parts


def current_git_commit(cwd: Path) -> str | None:
    """Return the current git commit when available."""
    try:
        proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True, check=False)
    except OSError:
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def find_project_root(run_directory: Path) -> Path:
    """Find the project root that owns a generated run directory."""
    resolved = run_directory.resolve()
    for candidate in [resolved, *resolved.parents]:
        if (candidate / "pyproject.toml").exists() and (candidate / "src" / "almgsi_dft").exists():
            return candidate
    return run_directory.parent


def run_case(config: WorkflowConfig, run_directory: Path, case_id: str, nprocs: int, *, force: bool = False) -> dict[str, Any]:
    """Run exactly one explicitly named local case."""
    project_root = find_project_root(run_directory)
    case_dir = run_directory / case_id
    if not case_dir.exists():
        raise RunError(f"Case directory does not exist: {case_dir}")
    pw_in = case_dir / "pw.in"
    if not pw_in.exists():
        raise RunError(f"Missing input file: {pw_in}")
    pw_out = case_dir / "pw.out"
    if pw_out.exists() and not force and parse_qe_output(pw_out).get("valid_result"):
        raise RunError(f"Refusing to overwrite completed output {pw_out}; pass --force to rerun")
    metadata = json.loads((case_dir / "metadata.json").read_text())
    ensure_pseudopotentials(config, required_symbols(config, metadata), project_root)
    command = resolve_qe_command(config, nprocs)
    status_path = case_dir / "run_status.json"
    status: dict[str, Any] = {
        "case_id": case_id,
        "status": "running",
        "start_time_utc": datetime.now(UTC).isoformat(),
        "command": command,
        "git_commit": current_git_commit(project_root),
    }
    status_path.write_text(json.dumps(status, indent=2))
    try:
        with pw_in.open("rb") as stdin, pw_out.open("wb") as stdout, (case_dir / "pw.err").open("wb") as stderr:
            proc = subprocess.run(command, cwd=case_dir, stdin=stdin, stdout=stdout, stderr=stderr, check=False)
    except KeyboardInterrupt:
        status |= {"status": "interrupted", "finish_time_utc": datetime.now(UTC).isoformat()}
        status_path.write_text(json.dumps(status, indent=2))
        raise
    parsed = parse_qe_output(pw_out)
    if parsed.get("valid_result"):
        export_relaxed_cif(pw_out, case_dir / "structure_final.cif")
    status |= parsed | {
        "returncode": proc.returncode,
        "status": "completed" if parsed.get("valid_result") else "failed",
        "finish_time_utc": datetime.now(UTC).isoformat(),
    }
    status_path.write_text(json.dumps(status, indent=2))
    return status


def run_case_list(
    config: WorkflowConfig, run_directory: Path, case_list: Path, nprocs: int, failure_limit: int = 1
) -> int:
    """Run an explicit case list sequentially; never discover all cases implicitly."""
    case_ids = [line.strip() for line in case_list.read_text().splitlines() if line.strip() and not line.startswith("#")]
    if not case_ids:
        raise RunError("Case list is empty; refusing to run implicit production set")
    print("Warning: production DFT calculations may be computationally expensive.")
    print(f"Run set contains {len(case_ids)} explicit cases. Cases will run sequentially.")
    failures = 0
    completed = 0
    total = len(case_ids)
    for index, case_id in enumerate(case_ids, start=1):
        remaining_after_this = total - index
        print(f"[{index}/{total}] START {case_id} (remaining after this: {remaining_after_this})", flush=True)
        start = perf_counter()
        try:
            status = run_case(config, run_directory, case_id, nprocs)
        except Exception as exc:
            failures += 1
            elapsed = _format_elapsed(perf_counter() - start)
            print(
                f"[{index}/{total}] FAILED {case_id} after {elapsed}: {exc}. "
                f"Completed {completed}/{total}; remaining {remaining_after_this}; failures {failures}/{failure_limit}.",
                flush=True,
            )
            if failures >= failure_limit:
                print(f"Stopping after failure limit {failure_limit}")
                return 1
            continue

        elapsed = _format_elapsed(perf_counter() - start)
        valid_result = bool(status.get("valid_result"))
        status_label = str(status.get("status", "unknown"))
        if status_label == "completed" and valid_result:
            completed += 1
            print(
                f"[{index}/{total}] DONE {case_id} after {elapsed}. "
                f"Completed {completed}/{total}; remaining {remaining_after_this}.",
                flush=True,
            )
        else:
            failures += 1
            print(
                f"[{index}/{total}] FINISHED WITH INVALID RESULT {case_id} after {elapsed} "
                f"(status={status_label}, valid={valid_result}). "
                f"Completed {completed}/{total}; remaining {remaining_after_this}; failures {failures}/{failure_limit}.",
                flush=True,
            )
            if failures >= failure_limit:
                print(f"Stopping after failure limit {failure_limit}")
                return 1
    print(f"Run set finished. Valid completed cases: {completed}/{total}; failures: {failures}.")
    return 0


def _format_elapsed(seconds: float) -> str:
    """Format elapsed runtime for human-readable progress messages."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, remainder = divmod(seconds, 60)
    if minutes < 60:
        return f"{int(minutes)}m {remainder:.0f}s"
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours)}h {int(minutes)}m"
