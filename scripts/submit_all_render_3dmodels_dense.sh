#!/bin/bash
# Submit all render_3dmodels_dense distributed rendering jobs
# Usage: cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse && \
#        bash scripts/submit_all_render_3dmodels_dense.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Submitting all render_3dmodels_dense distributed rendering jobs..."
echo ""

# Find all render_3dmodels_dense_*.sh scripts (excluding test split scripts)
# This will match both 0_50 and 7000_7050 patterns
for script in "${SCRIPT_DIR}"/render_3dmodels_dense_[0-9]*_[0-9]*.sh; do
  if [ -f "$script" ]; then
    echo "Submitting: $(basename $script)"
    sbatch "$script"
  fi
done

echo ""
echo "All jobs submitted!"
echo "Check status with: squeue -u \$USER"
