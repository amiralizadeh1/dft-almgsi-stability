PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip
CONFIG_SMOKE ?= config/local_smoke.yaml
SMOKE_RUN ?= runs/smoke

install:
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src tests

check-environment:
	bash scripts/check_environment.sh $(CONFIG_SMOKE)

generate-smoke:
	$(PYTHON) -m almgsi_dft.cli generate --config $(CONFIG_SMOKE) --output $(SMOKE_RUN)

run-smoke:
	$(PYTHON) -m almgsi_dft.cli run-local --run-directory $(SMOKE_RUN) --case smoke_al_fcc_primitive_scf --nprocs 1

collect-smoke:
	$(PYTHON) -m almgsi_dft.cli collect --run-directory $(SMOKE_RUN) --output results/smoke_results.csv

generate-convergence:
	$(PYTHON) -m almgsi_dft.cli generate --config config/convergence.yaml --output runs/convergence

analyse:
	$(PYTHON) -m almgsi_dft.cli analyse --results results/results.csv --output-directory results

report:
	$(PYTHON) -m almgsi_dft.cli report --results results/results.csv --output results/RESULTS.md

archive-results:
	bash scripts/archive_results.sh results figures runs results_archive.tar.gz

clean-generated:
	rm -rf runs/smoke runs/convergence results/*.csv results/*.md results/*.json figures/*.png figures/*.pdf
