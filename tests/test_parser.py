from almgsi_dft.parser import parse_qe_output


def test_parser_requires_job_done(tmp_path):
    path = tmp_path / "pw.out"
    path.write_text("!    total energy              =     -10.0 Ry\nconvergence has been achieved in 6 iterations\n")
    parsed = parse_qe_output(path)
    assert parsed["total_energy_ev"] is not None
    assert parsed["valid_result"] is False


def test_parser_accepts_complete_synthetic_snippet(tmp_path):
    path = tmp_path / "pw.out"
    path.write_text(
        "number of atoms/cell = 1\n"
        "!    total energy              =     -10.0 Ry\n"
        "convergence has been achieved in 6 iterations\n"
        "JOB DONE.\n"
    )
    parsed = parse_qe_output(path)
    assert parsed["job_done"] is True
    assert parsed["scf_iterations"] == 6
    assert parsed["valid_result"] is True
