import shutil
from pathlib import Path

import pytest

from almgsi_dft.config import load_config


@pytest.mark.integration
def test_optional_qe_environment_available():
    if shutil.which("pw.x") is None:
        pytest.skip("pw.x not available")
    cfg = load_config(Path("config/local_smoke.yaml"))
    if not any(cfg.pseudo_dir(Path.cwd()).glob("*.UPF")):
        pytest.skip("No pseudopotentials available")
    assert shutil.which("pw.x")
