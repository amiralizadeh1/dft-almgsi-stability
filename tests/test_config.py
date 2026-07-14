from pathlib import Path

import pytest

from almgsi_dft.config import load_config, validate_config
from almgsi_dft.exceptions import ConfigError


def test_smoke_config_warns():
    cfg = load_config(Path("config/local_smoke.yaml"))
    warnings = validate_config(cfg)
    assert any("unconverged" in warning for warning in warnings)


def test_malformed_configuration(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("[")
    with pytest.raises(ConfigError):
        load_config(path)


def test_unresolved_production_setting_rejected(tmp_path):
    path = tmp_path / "production.yaml"
    path.write_text(
        "profile: production\n"
        "settings: {input_dft: PBE, ecutwfc_ry: CHOOSE_ME}\n"
        "pseudopotentials: {files: {Al: CHOOSE_ME}}\n"
    )
    with pytest.raises(ConfigError):
        validate_config(load_config(path))
