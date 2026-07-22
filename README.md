# First-Principles Stability and Early Solute Clustering in Al-Mg-Si

This repository automates a small Quantum ESPRESSO plus ASE Density Functional Theory workflow for early Mg-Si clustering in aluminium. It supports a local Linux/WSL workflow for setup, convergence testing, input generation, parsing and analysis, and it also records the minimal Young HPC deployment used to complete the two heavier Mg-Si pair calculations.

The scientific workflow remains Python-driven and reproducible: ASE generates Quantum ESPRESSO inputs, `pw.x` performs the DFT calculations, and the Python tools collect, analyse and report the results. For local execution, the runner can launch `pw.x` directly under WSL/Linux. For HPC execution, this repository includes sanitized SGE/Young job-script templates under `hpc/young/` showing how the existing generated `pw.in` files were run with `qsub`, `gerun` and the Young Quantum ESPRESSO module. Pseudopotentials and private HPC details such as usernames, allocations, SSH keys, Scratch paths and job IDs are intentionally not committed.

## Scientific Motivation
Al-Mg-Si alloys strengthen through solute clustering and precipitation. The earliest Mg-Si associations influence later precipitation pathways, but their energetics are hard to isolate experimentally. DFT gives controlled zero-temperature total-energy differences for elemental references, isolated solutes and Mg-Si pairs.

## Research Question
Are Mg and Si substitutions in FCC Al energetically attracted at first-neighbour, second-neighbour or larger separations in a 32-site 2x2x2 conventional FCC Al supercell?

## Why DFT Is Useful
First-principles calculations isolate electronic total-energy trends for well-defined atomic configurations. Those pair-binding trends can later inform precipitation, Monte Carlo or kinetic Monte Carlo models, after validation and enough configuration coverage.

## Energy Equations
Substitution formation energy:

```text
E_f(X_Al) = E(Al_(N-1)X) - E(Al_N) + mu_Al - mu_X
```

Pair-binding energy:

```text
E_bind(r) = E(Al_(N-1)Mg) + E(Al_(N-1)Si) - E(Al_(N-2)MgSi; r) - E(Al_N)
```

Positive `E_bind` means attraction. Negative `E_bind` means the pair is less stable than separated substitutions under the same reference convention. `mu_Al`, `mu_Mg` and `mu_Si` are zero-temperature DFT bulk reference chemical potentials from optimised elemental structures, not finite-temperature thermodynamic chemical potentials.

## Repository Structure

```text
dft-almgsi-stability/
├── src/almgsi_dft/          # Python workflow: config, structures, QE inputs, local runner, parsing, energetics, analysis, reporting
├── config/                  # Smoke, convergence and production YAML profiles
├── hpc/young/               # Sanitized Young SGE job templates and deployment notes
│   ├── README.md
│   ├── run_al30mgsi_1nn.template.sh
│   └── run_al30mgsi_2nn.template.sh
├── pseudos/                 # Local SSSP Efficiency UPF files (required at runtime, not committed)
├── runs/                    # Generated QE case directories and selected outputs
├── results/                 # Collected CSVs, binding-energy tables, plots and RESULTS.md
├── figures/                 # Optional figure outputs
├── scripts/                 # Helper scripts
└── tests/                   # Unit and integration tests
```

`src/almgsi_dft` contains the scientific workflow. `config` holds editable YAML profiles. `hpc/young` documents the minimal Young Tier-2 deployment: sanitized SGE/`qsub` job templates for `Al30MgSi_1NN` and `Al30MgSi_2NN`, using `gerun` and the Young Quantum ESPRESSO module. Private run scripts, usernames, allocations, SSH keys, Scratch paths and job IDs are intentionally not committed. `pseudos` stores manually downloaded UPF files needed by `pw.x`. `runs`, `results` and `figures` hold generated inputs, selected outputs, tables, reports and plots.

## Local Execution Model
This project can be edited from Windows, but the recommended local calculation runtime is WSL/Linux because Quantum ESPRESSO is normally installed and run as a Linux scientific code. The Python workflow prepares inputs, launches `pw.x`, parses outputs and writes tables/reports. Quantum ESPRESSO does the actual DFT calculation.

There are three separate pieces:

- The project folder, for example `/mnt/c/Users/YOUR_WINDOWS_USER/dft-almgsi-stability` when accessed from WSL.
- A Python virtual environment, preferably on the WSL Linux filesystem.
- Quantum ESPRESSO, which provides the `pw.x` executable.

## HPC Execution Model
Heavier production cases, especially `Al30MgSi_1NN` and `Al30MgSi_2NN`, may exceed ordinary laptop/WSL resources. For those cases this repository records a minimal Young HPC deployment that runs the existing generated `pw.in` files directly on compute nodes. The scientific settings are not regenerated or altered on the cluster.

The HPC path uses several separate pieces:

- SSH access to the Young login node.
- A Scratch-based clone of this repository.
- Separately transferred UPF pseudopotentials in `pseudos/`.
- Young environment modules for Quantum ESPRESSO and MPI.
- Sanitized SGE job-script templates under `hpc/young/`.
- Scheduler submission with `qsub`, monitoring with `qstat`, and MPI launch with `gerun`.

Typical Young workflow:

1. Clone or pull the repository under Scratch.
2. Transfer only the required UPF files into `pseudos/`.
3. Copy a sanitized template into a private local script:

```bash
cp hpc/young/run_al30mgsi_1nn.template.sh hpc/young/run_al30mgsi_1nn.sh
```

4. Replace `YOUR_YOUNG_PROJECT` with the project/allocation name returned by `budgets`.
5. Submit from the repository root:

```bash
qsub hpc/young/run_al30mgsi_1nn.sh
qstat -u "$USER"
```

6. Confirm success with `JOB DONE` in `pw.out` and a clean scheduler exit status.
7. Copy completed `pw.out` files back to the local repository and run the existing Python `collect`, `analyse` and `report` commands locally.

Validated Young settings for the completed pair cases were SGE/`qsub`, `gerun`, `quantum-espresso/6.5-impi/intel-2018`, PWSCF v6.5 and 8 MPI ranks. Private details such as usernames, allocations, SSH keys, full Scratch paths, node names and job IDs are intentionally omitted from the public templates. See `hpc/young/README.md` for the template details.

## Install Quantum ESPRESSO Under WSL Or Linux
On Ubuntu/WSL, install QE with:

```bash
sudo apt update
sudo apt install quantum-espresso
```

Check that `pw.x` is available:

```bash
which pw.x
pw.x -h
```

If `which pw.x` prints a path such as `/usr/bin/pw.x`, QE is visible to the runner. You may also set:

```bash
export QE_PW_COMMAND="pw.x"
```

Local commands such as `mpirun -np 4 pw.x` are accepted as an executable command string. Cluster execution uses the separate Young SGE templates in `hpc/young/` rather than the local Python runner.

## Create The Python Virtual Environment In WSL
If the project is stored on the Windows drive, do not create the Linux virtual environment inside `/mnt/c/...`. Create it inside your WSL home directory instead:

```bash
mkdir -p ~/venvs
python3 -m venv ~/venvs/dft-almgsi-stability
source ~/venvs/dft-almgsi-stability/bin/activate
```

Then go to the project folder. If the repository is in `C:\Users\YOUR_WINDOWS_USER\dft-almgsi-stability`, the WSL path is:

```bash
cd /mnt/c/Users/YOUR_WINDOWS_USER/dft-almgsi-stability
```

Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If editable installation fails on `/mnt/c/...` with an `Operation not permitted` error, use `PYTHONPATH` instead:

```bash
export PYTHONPATH=/mnt/c/Users/YOUR_WINDOWS_USER/dft-almgsi-stability/src:$PYTHONPATH
```

You can add that line to `~/.bashrc`, but if sourcing `~/.bashrc` removes the virtual-environment prompt, simply activate the environment again:

```bash
source ~/venvs/dft-almgsi-stability/bin/activate
```

If the project is copied into the WSL Linux filesystem, for example `~/dft-almgsi-stability`, then `pip install -e .` is usually fine.

## Obtain And Configure SSSP Pseudopotentials
Manually download compatible Al, Mg and Si pseudopotentials from the SSSP Efficiency collection. Do not commit them. Do not use placeholder names as real filenames.

```bash
cp config/pseudopotentials.example.yaml config/pseudopotentials.yaml
# edit the exact filenames into config/local_smoke.yaml, config/convergence.yaml or config/production.yaml
```

The code fails clearly when a required pseudopotential is missing.

For the smoke test, `config/local_smoke.yaml` needs the exact Al pseudopotential filename:

```yaml
pseudopotentials:
  pseudo_dir: pseudos
  files:
    Al: Al.us.pbe.z_3.ld1.psl.v1.0.0-low.upf
```

The file itself must exist in:

```text
pseudos/
```

WSL/Linux filenames are case-sensitive, so `.UPF` and `.upf` are different names.

## Unit Tests And Lint

```bash
python -m pytest
python -m ruff check src tests
```

Ordinary tests do not require Quantum ESPRESSO or pseudopotentials. One integration test is marked and skipped unless `pw.x` and valid pseudopotentials are present.

## Smoke Test
`config/local_smoke.yaml` is scientifically unconverged and deliberately small. It generates only one primitive FCC Al SCF input, optionally with `nstep = 0`.

Start each WSL session with:

```bash
cd /mnt/c/Users/YOUR_WINDOWS_USER/dft-almgsi-stability
source ~/venvs/dft-almgsi-stability/bin/activate
export PYTHONPATH=/mnt/c/Users/YOUR_WINDOWS_USER/dft-almgsi-stability/src:$PYTHONPATH
```

Generate the smoke input:

```bash
python -m almgsi_dft.cli generate --config config/local_smoke.yaml --output runs/smoke
```

Expected output:

```text
Generated 1 case directories in runs/smoke
```

List the generated case:

```bash
python -m almgsi_dft.cli list-cases --run-directory runs/smoke
```

Expected output:

```text
smoke_al_fcc_primitive_scf
```

Run the explicit smoke case:

```bash
python -m almgsi_dft.cli run-local --run-directory runs/smoke --case smoke_al_fcc_primitive_scf --nprocs 1
```

The run may print little or nothing to the terminal. Check status:

```bash
python -m almgsi_dft.cli status --run-directory runs/smoke
```

Expected successful output:

```text
smoke_al_fcc_primitive_scf: completed valid=True
```

Also check the QE output directly:

```bash
grep "JOB DONE" runs/smoke/smoke_al_fcc_primitive_scf/pw.out
grep "convergence has been achieved" runs/smoke/smoke_al_fcc_primitive_scf/pw.out
```

Collect the smoke result:

```bash
python -m almgsi_dft.cli collect --run-directory runs/smoke --output results/smoke_results.csv
cat results/smoke_results.csv
```

Look for `valid_result` equal to `True`. This means the smoke calculation ran, converged electronically and ended with QE's `JOB DONE` marker. The smoke test is only a software and installation check. It is not a meaningful DFT result.

After a successful smoke run, the case directory should contain `pw.in`, `pw.out`, `pw.err`, `metadata.json`, `run_status.json` and `structure_initial.cif`. The most important success checks are `valid_result: true` in `run_status.json`, `JOB DONE` in `pw.out` and an empty or non-critical `pw.err`.

## Lessons Learned During Smoke Setup
These were the practical issues encountered during the first local smoke setup and how to fix them.

`ModuleNotFoundError: No module named 'almgsi_dft'` means Python can see the dependencies but not this project package. Fix it with `pip install -e .` when the project is on a Linux filesystem, or set `PYTHONPATH=/path/to/project/src` when working from `/mnt/c/...`.

`Python was not found; run without arguments to install from the Microsoft Store` means the command was run in Windows PowerShell, not WSL. Open WSL first with `wsl`, then use `python3`.

`wsl --status` showing `Default Version: 2` only means WSL 2 is configured. If `wsl` says no distributions are installed, install one with `wsl --install -d Ubuntu` from PowerShell and reboot if Windows asks.

`python3 -m venv .venv-wsl` failing under `/mnt/c/...` is a Windows-filesystem permission issue. Create the WSL virtual environment in the Linux home directory, for example `~/venvs/dft-almgsi-stability`, then run the project from `/mnt/c/...`.

`source ~/.bashrc` can make the virtual-environment prompt disappear because it reloads shell settings. Activate the environment again with `source ~/venvs/dft-almgsi-stability/bin/activate`.

`Missing required pseudopotentials` means the filename in the YAML config does not match a file in `pseudos/`, or the path is being resolved incorrectly. Current generated QE inputs use relative Linux-style paths such as `../../../pseudos`.

`Error in routine readpp` from QE means Quantum ESPRESSO started, but could not read the pseudopotential file. Check the `pseudo_dir` line in `pw.in`, check the exact filename, and remember that WSL paths are case-sensitive.

`[WinError 2] The system cannot find the file specified` in PowerShell means Windows could not find `pw.x`. Run the calculation in WSL after installing `quantum-espresso`, or set `QE_PW_COMMAND` to a valid Windows QE executable if using a native Windows build.

## Cut-Off And K-Point Convergence
Cut-off convergence varies `ecutwfc` at a fixed k-point grid. K-point convergence varies the grid at selected cut-offs. The example `0.001 eV/atom` threshold is only a diagnostic and never a universal convergence claim.

```bash
cp config/convergence.example.yaml config/convergence.yaml
# edit pseudopotentials and settings
python -m almgsi_dft.cli generate --config config/convergence.yaml --output runs/convergence
python -m almgsi_dft.cli run-local --run-directory runs/convergence --case conv_cutoff_al_ecut40 --nprocs 1
```

Current convergence settings selected for production are `ecutwfc = 50 Ry`, `ecutrho = 400 Ry` and `kpoints = [8, 8, 8]`. These were chosen after running the generated cutoff cases at 30, 40, 50 and 60 Ry and k-point cases at 4x4x4, 6x6x6 and 8x8x8. The collected convergence outputs are in `results/convergence_results.csv`, `results/cutoff_convergence.csv` and `results/kpoint_convergence.csv`.

## Elemental Structures And Production Inputs
Elemental references support `vc-relax` for FCC Al, HCP Mg and diamond Si. Fixed-cell defect relaxations use the configured optimised Al lattice constant.

```bash
cp config/production.example.yaml config/production.yaml
# replace all CHOOSE_ME, UNRESOLVED, null and pseudopotential placeholders
python -m almgsi_dft.cli validate-config --config config/production.yaml
python -m almgsi_dft.cli generate --config config/production.yaml --output runs/production
```

Generation never launches calculations. Complete 32-atom relaxations and convergence studies may take substantial time on an ordinary laptop.

Current production state:

- Completed valid production calculations: `ref_Al_fcc`, `ref_Mg_hcp`, `ref_Si_diamond`, `Al32`, `Al31Mg`, `Al31Si`, `Al30MgSi_1NN`, `Al30MgSi_2NN` and `Al30MgSi_far`.
- `Al30MgSi_1NN` and `Al30MgSi_2NN` initially stopped during local WSL runs around the first SCF step without a QE fatal error or `JOB DONE` marker. The existing generated `pw.in` files were then run unchanged on the UCL Young Tier-2 HPC facility.
- No structures, DFT settings, pseudopotentials, cutoffs, k-points, smearing settings, convergence thresholds or relaxation settings were changed for the Young runs.
- Final Mg-Si pair binding energies, where positive values indicate attraction, are: `1NN = 0.0426 eV` at `2.8603 Angstrom`, `2NN = 0.0066 eV` at `4.0500 Angstrom` and `far = 0.0229 eV` at `7.0148 Angstrom`.

Each production case directory under `runs/production/<case_id>/` contains `pw.in`, `metadata.json`, `run_status.json`, `structure_initial.cif` and, after execution, `pw.out`, `pw.err` and usually `structure_final.cif` for valid relaxations. `run_status.json` is the quickest status check; `pw.out` should contain `JOB DONE` for a successful QE run.

## Young HPC Completion
The heavy `Al30MgSi_1NN` and `Al30MgSi_2NN` calculations were completed on the UCL Young Tier-2 HPC facility after the local WSL attempts did not finish. The Young runs used the existing generated QE inputs directly:

```bash
gerun pw.x -in pw.in > pw.out 2> pw.err
```

The Young environment used SGE/`qsub`, `gerun`, Quantum ESPRESSO `pw.x` from `quantum-espresso/6.5-impi/intel-2018`, PWSCF v6.5 and 8 MPI ranks per case. The non-invasive job scripts are stored in `hpc/young/`. They document the module loading, MPI launch command and output handling used for these two cases without changing the scientific workflow.

The Young-completed `pw.out` and `pw.err` files were copied back into the local `runs/production/Al30MgSi_1NN/` and `runs/production/Al30MgSi_2NN/` folders, parsed locally with the existing Python workflow, and included in the final `results/results.csv`, `results/pair_binding_energies.csv` and `results/RESULTS.md` outputs.

## Run One Calculation Locally

```bash
python -m almgsi_dft.cli run-local --run-directory runs/production --case Al30MgSi_1NN --nprocs 1
```

## Run An Explicit Sequential List

```bash
printf "Al32\nAl31Mg\nAl31Si\n" > case_list.txt
python -m almgsi_dft.cli run-set --run-directory runs/production --case-list case_list.txt --nprocs 1
```

`run-set` runs sequentially, never uses multiprocessing and never runs all generated cases implicitly.

## Monitor, Collect, Analyse And Report

```bash
python -m almgsi_dft.cli status --run-directory runs/production
python -m almgsi_dft.cli collect --run-directory runs/production --output results/results.csv
python -m almgsi_dft.cli analyse --results results/results.csv --output-directory results
python -m almgsi_dft.cli report --results results/results.csv --output results/RESULTS.md
```

Invalid or incomplete calculations remain in the CSV with `valid_result = false` and are excluded from physical energy analysis. The report does not claim agreement with experiment unless validation is later supplied.

## Archive Publication-Ready Results

```bash
make archive-results
```

The archive excludes pseudopotentials, wavefunctions, QE scratch directories, large binaries and `.venv`.

## Limitations And Future Extensions
No fake QE outputs are included. No DFT result is invented, estimated or interpolated. Future KMC or Monte Carlo work could use validated binding trends as model inputs. Full scheduler integration inside the Python CLI is not implemented; Young HPC execution currently uses external SGE templates that launch `pw.x` on existing generated inputs. The code still separates structure generation, input generation, parsing and analysis so a native HPC execution layer could be added later without rewriting the science modules.

## References
- Quantum ESPRESSO documentation.
- ASE documentation.
- SSSP Efficiency pseudopotential library.
- Perdew, Burke and Ernzerhof, generalized gradient approximation.

## Citation And Acknowledgements
Quantum ESPRESSO requests citation of:

- P. Giannozzi et al., Journal of Physics: Condensed Matter 21, 395502 (2009).
- P. Giannozzi et al., Journal of Physics: Condensed Matter 29, 465901 (2017).
- See also: <http://www.quantum-espresso.org/quote>.

Calculations completed on Young should acknowledge the facility using:

```text
We are grateful to the UK Materials and Molecular Modelling Hub for computational resources, which is partially funded by EPSRC (EP/T022213/1, EP/W032260/1 and EP/P020194/1).
```

If MCC or UKCP resources were used, follow the combined acknowledgement guidance in the Young documentation: <https://www.rc.ucl.ac.uk/docs/Clusters/Young/#acknowledging-the-use-of-young-in-publications>.
