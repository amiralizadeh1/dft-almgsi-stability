#!/usr/bin/env bash
set -euo pipefail
RESULTS_DIR="${1:-results}"
FIGURES_DIR="${2:-figures}"
RUNS_DIR="${3:-runs}"
ARCHIVE="${4:-almgsi_results_archive.tar.gz}"

tar --exclude='.venv' \
  --exclude='pseudos/*.UPF' \
  --exclude='*.save' \
  --exclude='*.wfc*' \
  --exclude='qe_tmp' \
  --exclude='tmp' \
  --exclude='*.dat' \
  --exclude='*.mix*' \
  --exclude='*.tar.gz' \
  -czf "$ARCHIVE" README.md pyproject.toml config pseudos/README.md "$RESULTS_DIR" "$FIGURES_DIR" "$RUNS_DIR" 2>/dev/null || true

echo "Created $ARCHIVE without pseudopotentials, wavefunctions or QE scratch directories."
