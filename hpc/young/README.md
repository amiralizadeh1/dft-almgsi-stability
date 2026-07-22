# Young HPC Job Templates

This directory contains sanitized SGE job-script templates for running the two heavy Mg-Si pair calculations on UCL Young:

- `run_al30mgsi_1nn.template.sh`
- `run_al30mgsi_2nn.template.sh`

The templates are safe to commit because they do not include usernames, private paths, node names, job IDs or allocation names. They assume the repository is cloned under:

```text
$HOME/Scratch/dft-almgsi-stability
```

## Preparing Private Run Scripts

On Young, copy a template to a private script:

```bash
cp hpc/young/run_al30mgsi_1nn.template.sh hpc/young/run_al30mgsi_1nn.sh
cp hpc/young/run_al30mgsi_2nn.template.sh hpc/young/run_al30mgsi_2nn.sh
```

Then replace:

```text
YOUR_YOUNG_PROJECT
```

with the exact project/allocation name reported by:

```bash
budgets
```

The private `*.sh` files are ignored by Git so account-specific details are not published.

## Validated Environment

The completed Young runs used:

- SGE / `qsub`
- `gerun`
- `quantum-espresso/6.5-impi/intel-2018`
- PWSCF v6.5
- 8 MPI ranks
- existing generated `pw.in` files

The templates run Quantum ESPRESSO directly:

```bash
gerun pw.x -in pw.in > pw.out 2> pw.err
```

They do not regenerate structures or modify DFT settings.
