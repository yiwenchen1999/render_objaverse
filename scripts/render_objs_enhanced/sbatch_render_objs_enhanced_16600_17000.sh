#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

JOB_SCRIPTS=(
  "${SCRIPT_DIR}/render_objs_enhanced_16000_16100.sh"
  "${SCRIPT_DIR}/render_objs_enhanced_16100_16200.sh"
  "${SCRIPT_DIR}/render_objs_enhanced_16200_16300.sh"
  "${SCRIPT_DIR}/render_objs_enhanced_16300_16400.sh"
  "${SCRIPT_DIR}/render_objs_enhanced_16400_16500.sh"
  "${SCRIPT_DIR}/render_objs_enhanced_16500_16600.sh"
  "${SCRIPT_DIR}/render_objs_enhanced_16600_16700.sh"
  "${SCRIPT_DIR}/render_objs_enhanced_16700_16800.sh"
  "${SCRIPT_DIR}/render_objs_enhanced_16800_16900.sh"
  "${SCRIPT_DIR}/render_objs_enhanced_16900_17000.sh"
)

for job_script in "${JOB_SCRIPTS[@]}"; do
  if [ ! -f "${job_script}" ]; then
    echo "Missing job script: ${job_script}"
    exit 1
  fi
done

echo "Submitting ${#JOB_SCRIPTS[@]} jobs for groups 16600-17000"
for job_script in "${JOB_SCRIPTS[@]}"; do
  echo "sbatch ${job_script}"
  sbatch "${job_script}"
done

echo "All 16600-17000 jobs submitted."
