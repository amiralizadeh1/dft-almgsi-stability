from pathlib import Path

from almgsi_dft import runner


def test_run_case_list_prints_progress(monkeypatch, tmp_path, capsys):
    case_list = tmp_path / "cases.txt"
    case_list.write_text("Al31Mg\nAl31Si\n")
    calls: list[str] = []

    def fake_run_case(config, run_directory: Path, case_id: str, nprocs: int):
        calls.append(case_id)
        return {"case_id": case_id, "status": "completed", "valid_result": True}

    monkeypatch.setattr(runner, "run_case", fake_run_case)

    exit_code = runner.run_case_list(object(), tmp_path, case_list, nprocs=1)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert calls == ["Al31Mg", "Al31Si"]
    assert "Run set contains 2 explicit cases" in output
    assert "[1/2] START Al31Mg" in output
    assert "[1/2] DONE Al31Mg" in output
    assert "Completed 2/2" in output
    assert "Run set finished" in output


def test_run_case_list_stops_after_invalid_result(monkeypatch, tmp_path, capsys):
    case_list = tmp_path / "cases.txt"
    case_list.write_text("Al31Mg\nAl31Si\n")

    def fake_run_case(config, run_directory: Path, case_id: str, nprocs: int):
        return {"case_id": case_id, "status": "failed", "valid_result": False}

    monkeypatch.setattr(runner, "run_case", fake_run_case)

    exit_code = runner.run_case_list(object(), tmp_path, case_list, nprocs=1, failure_limit=1)

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "FINISHED WITH INVALID RESULT Al31Mg" in output
    assert "Stopping after failure limit 1" in output
