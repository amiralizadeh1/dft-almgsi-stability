#!/bin/bash -l
#$ -N almgsi_1nn
#$ -cwd
#$ -P Gold
#$ -A YOUR_YOUNG_PROJECT
#$ -l h_rt=24:00:00
#$ -l mem=6G
#$ -pe mpi 8
#$ -o hpc/young/almgsi_1nn.$JOB_ID.out
#$ -e hpc/young/almgsi_1nn.$JOB_ID.err

set -euo pipefail

echo "Job started at: $(date)"
echo "Hostname: $(hostname)"
echo "Job ID: ${JOB_ID:-unknown}"
echo "NSLOTS: ${NSLOTS:-unknown}"
echo "Submission directory: ${SGE_O_WORKDIR:-unknown}"

# Fill YOUR_YOUNG_PROJECT from the output of `budgets` before submitting.
module load default-modules/2018
module unload gcc-libs/4.9.2 2>/dev/null || true
module load quantum-espresso/6.5-impi/intel-2018

echo "Loaded modules:"
module list 2>&1

echo "pw.x path:"
which pw.x

CASE_DIR="$HOME/Scratch/dft-almgsi-stability/runs/production/Al30MgSi_1NN"
cd "$CASE_DIR"

echo "Working directory: $(pwd)"
echo "Input file:"
ls -lh pw.in

timestamp="$(date +%Y%m%d_%H%M%S)"
if [ -e pw.out ]; then
  cp -p pw.out "pw.out.pre_young_${timestamp}"
fi
if [ -e pw.err ]; then
  cp -p pw.err "pw.err.pre_young_${timestamp}"
fi

echo "Starting Quantum ESPRESSO at: $(date)"
gerun pw.x -in pw.in > pw.out 2> pw.err
echo "Quantum ESPRESSO finished at: $(date)"

grep -n "JOB DONE" pw.out || true
