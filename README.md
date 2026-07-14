# First-Principles Stability and Early Solute Clustering in Al-Mg-Si

This local Linux/WSL repository automates a small Quantum ESPRESSO plus ASE Density Functional Theory workflow for early Mg-Si clustering in aluminium. It intentionally contains no HPC, scheduler, SSH, remote-transfer, Slurm, SGE, PBS, Young-specific or cluster implementation.

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
`src/almgsi_dft` contains configuration, structures, neighbour shells, QE input generation, local execution, parsing, energetics, convergence, analysis, plotting and reporting. `config` contains smoke and example profiles. `pseudos` is for manually downloaded SSSP Efficiency UPF files. `runs`, `results` and `figures` hold generated inputs and outputs.

## Local Execution Model
This project can be edited from Windows, but the recommended calculation runtime is WSL/Linux because Quantum ESPRESSO is normally installed and run as a Linux scientific code. The Python workflow prepares inputs, launches `pw.x`, parses outputs and writes tables/reports. Quantum ESPRESSO does the actual DFT calculation.

There are three separate pieces:

- The project folder, for example `/mnt/c/Users/YOUR_WINDOWS_USER/dft-almgsi-stability` when accessed from WSL.
- A Python virtual environment, preferably on the WSL Linux filesystem.
- Quantum ESPRESSO, which provides the `pw.x` executable.

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

Local commands such as `mpirun -np 4 pw.x` are accepted as an executable command string. No scheduler or cluster execution is implemented.

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

## Elemental Structures And Production Inputs
Elemental references support `vc-relax` for FCC Al, HCP Mg and diamond Si. Fixed-cell defect relaxations use the configured optimised Al lattice constant.

```bash
cp config/production.example.yaml config/production.yaml
# replace all CHOOSE_ME, UNRESOLVED, null and pseudopotential placeholders
python -m almgsi_dft.cli validate-config --config config/production.yaml
python -m almgsi_dft.cli generate --config config/production.yaml --output runs/production
```

Generation never launches calculations. Complete 32-atom relaxations and convergence studies may take substantial time on an ordinary laptop.

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
No fake QE outputs are included. No DFT result is invented, estimated or interpolated. Future KMC or Monte Carlo work could use validated binding trends as model inputs. Future HPC support is intentionally conceptual here: the code separates structure generation, input generation, parsing and analysis so a new execution layer could be added later without rewriting the science modules.

## References
- Quantum ESPRESSO documentation.
- ASE documentation.
- SSSP Efficiency pseudopotential library.
- Perdew, Burke and Ernzerhof, generalized gradient approximation.
