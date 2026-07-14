"""Configuration loading and validation."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .exceptions import ConfigError, MissingPseudopotentialError

UNRESOLVED = {None, "", "CHOOSE_ME", "UNRESOLVED"}


@dataclass(frozen=True)
class WorkflowConfig:
    """Parsed workflow configuration."""

    path: Path
    raw: dict[str, Any]

    @property
    def profile(self) -> str:
        return str(self.raw.get("profile", "unknown"))

    @property
    def settings(self) -> dict[str, Any]:
        return dict(self.raw.get("settings", {}))

    @property
    def cases(self) -> dict[str, Any]:
        return dict(self.raw.get("cases", {}))

    @property
    def pseudopotentials(self) -> dict[str, Any]:
        return dict(self.raw.get("pseudopotentials", {}))

    def pseudo_dir(self, base: Path | None = None) -> Path:
        """Return the configured pseudopotential directory."""
        base = base or self.path.parent.parent
        value = self.pseudopotentials.get("pseudo_dir") or self.settings.get("pseudo_dir") or "pseudos"
        path = Path(value)
        return path if path.is_absolute() else base / path

    def pseudo_files(self) -> dict[str, str]:
        """Return pseudopotential filename mapping."""
        return dict(self.pseudopotentials.get("files", {}))


def load_config(path: str | Path) -> WorkflowConfig:
    """Load a YAML workflow configuration."""
    config_path = Path(path)
    try:
        data = yaml.safe_load(config_path.read_text())
    except yaml.YAMLError as exc:
        raise ConfigError(f"Malformed YAML in {config_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"Configuration {config_path} must contain a YAML mapping")
    return WorkflowConfig(config_path, data)


def contains_unresolved(value: Any) -> bool:
    """Return True if a value contains unresolved placeholders."""
    if isinstance(value, str) and "PLACEHOLDER" in value:
        return True
    if isinstance(value, dict):
        return any(contains_unresolved(v) for v in value.values())
    if isinstance(value, list):
        return any(contains_unresolved(v) for v in value)
    if value in UNRESOLVED:
        return True
    return False


def validate_config(config: WorkflowConfig, *, require_pseudos_exist: bool = False) -> list[str]:
    """Validate a config and return human-readable warnings."""
    warnings: list[str] = []
    if config.settings.get("input_dft", "PBE") != "PBE":
        raise ConfigError("This workflow requires input_dft = PBE")
    if config.profile == "local_smoke":
        warnings.append("local_smoke is scientifically unconverged and only checks local plumbing.")
    if config.profile == "production" and contains_unresolved(config.raw):
        raise ConfigError("Production configuration contains unresolved placeholders/null values")
    required = required_symbols(config)
    missing = [symbol for symbol in required if contains_unresolved(config.pseudo_files().get(symbol))]
    if missing and config.profile != "local_smoke":
        raise ConfigError(f"Missing pseudopotential filename entries for: {', '.join(missing)}")
    if config.cases.get("include_defects") and not config.settings.get("ecutwfc_ry"):
        raise ConfigError("Defect calculations require explicitly selected convergence settings")
    if require_pseudos_exist:
        ensure_pseudopotentials(config, required)
    return warnings


def required_symbols(config: WorkflowConfig, metadata: dict[str, Any] | None = None) -> set[str]:
    """Return symbols required by a configuration or specific case."""
    if metadata and metadata.get("required_symbols"):
        return set(metadata["required_symbols"])
    if config.profile == "local_smoke":
        return {"Al"}
    symbols = {"Al"}
    if config.cases.get("include_elemental_refs") or config.cases.get("include_defects"):
        symbols |= {"Mg", "Si"}
    return symbols


def ensure_pseudopotentials(
    config: WorkflowConfig, symbols: set[str], base: Path | None = None
) -> None:
    """Fail clearly if required pseudopotential files are missing."""
    pseudo_dir = config.pseudo_dir(base)
    pseudo_files = config.pseudo_files()
    missing: list[str] = []
    for symbol in symbols:
        filename = pseudo_files.get(symbol)
        if contains_unresolved(filename):
            missing.append(f"{symbol}: unresolved filename")
        elif not (pseudo_dir / str(filename)).exists():
            missing.append(f"{symbol}: {pseudo_dir / str(filename)}")
    if missing:
        raise MissingPseudopotentialError("Missing required pseudopotentials: " + "; ".join(missing))
