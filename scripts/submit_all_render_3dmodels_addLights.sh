#!/bin/bash
# Submit all render_3dmodels_addLights distributed rendering jobs
# Usage: cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse && \
#        bash scripts/submit_all_render_3dmodels_addLights.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Submitting all render_3dmodels_addLights distributed rendering jobs..."
echo ""

# Find all render_3dmodels_addLights_*.sh scripts
for script in "${SCRIPT_DIR}"/render_3dmodels_addLights_[0-9]*_[0-9]*.sh; do
  if [ -f "$script" ]; then
    echo "Submitting: $(basename $script)"
    sbatch "$script"
  fi
done

echo ""
echo "All jobs submitted!"
echo "Check status with: squeue -u \$USER"
