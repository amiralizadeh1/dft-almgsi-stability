#!/usr/bin/env bash
set -euo pipefail
CONFIG_FILE="${1:-config/local_smoke.yaml}"

echo "Checking Python..."
python3 --version || { echo "Install Python 3.11 or newer."; exit 1; }

echo "Checking Quantum ESPRESSO command..."
QE_CMD="${QE_PW_COMMAND:-pw.x}"
if ! command -v "${QE_CMD%% *}" >/dev/null 2>&1; then
  echo "Warning: ${QE_CMD%% *} was not found on PATH. Set QE_PW_COMMAND or install Quantum ESPRESSO."
fi

echo "Checking Python dependencies..."
python3 - <<'PY'
missing = []
for module in ["ase", "numpy", "scipy", "pandas", "matplotlib", "yaml"]:
    try:
        __import__(module)
    except Exception:
        missing.append(module)
if missing:
    print("Missing Python modules:", ", ".join(missing))
    raise SystemExit(1)
print("Python dependencies are importable.")
PY

echo "Checking pseudopotential configuration..."
python3 -m almgsi_dft.cli validate-config --config "$CONFIG_FILE" || true
echo "No calculations were performed."
