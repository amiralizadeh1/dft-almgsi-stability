from pathlib import Path

import yaml

from almgsi_dft.config import load_config
from almgsi_dft.qe_inputs import generate_run


def test_smoke_qe_input_generation(tmp_path):
    cfg = load_config(Path("config/local_smoke.yaml"))
    generated = generate_run(cfg, tmp_path / "run")
    assert len(generated) == 1
    case = generated[0]
    assert (case / "pw.in").exists()
    text = (case / "pw.in").read_text()
    assert "PBE" in text
    assert "Users" not in text
    assert "lenovo" not in text
    pseudo_line = next(line for line in text.splitlines() if "pseudo_dir" in line)
    assert "\\" not in pseudo_line
    assert "pseudos" in pseudo_line
    assert (case / "metadata.json").exists()
    copied_config = yaml.safe_load((tmp_path / "run" / "config.yaml").read_text())
    assert copied_config["pseudopotentials"]["pseudo_dir"] == "pseudos"


def test_generate_does_not_run_all_cases(tmp_path):
    cfg = load_config(Path("config/local_smoke.yaml"))
    generate_run(cfg, tmp_path / "run")
    assert not (tmp_path / "run" / "smoke_al_fcc_primitive_scf" / "pw.out").exists()
