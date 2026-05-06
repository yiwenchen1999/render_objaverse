#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Submit only ranged enhanced jobs, e.g. render_objs_enhanced_15000_15100.sh
mapfile -t JOB_SCRIPTS < <(ls "${SCRIPT_DIR}"/render_objs_enhanced_[0-9]*_[0-9]*.sh 2>/dev/null | sort -V)

if [ "${#JOB_SCRIPTS[@]}" -eq 0 ]; then
  echo "No ranged enhanced job scripts found in ${SCRIPT_DIR}"
  exit 1
fi

echo "Submitting ${#JOB_SCRIPTS[@]} jobs from ${SCRIPT_DIR}"
for job_script in "${JOB_SCRIPTS[@]}"; do
  echo "sbatch ${job_script}"
  sbatch "${job_script}"
done

echo "All jobs submitted."
