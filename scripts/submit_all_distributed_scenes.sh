#!/bin/bash
# =============================================================================
# Submit all distributed scene rendering jobs to Explorer cluster
# Usage: bash scripts/submit_all_distributed_scenes.sh
# =============================================================================

set -euo pipefail

cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

# Check if distributed scripts exist
if [ ! -f scripts/distribute_render_3dscenes_0_50.sh ]; then
  echo "Error: Distributed scripts not found. Run scripts/generate_all_distributed_scripts.sh first."
  exit 1
fi

# Submit all jobs
for script in scripts/distribute_render_3dscenes_*.sh; do
  if [[ "$script" == *"distribute_render_3dscenes_"* ]]; then
    echo "Submitting: $script"
    sbatch "$script"
    sleep 1  # Avoid overwhelming the scheduler
  fi
done

echo ""
echo "All jobs submitted!"
echo "Check status: squeue -u \$USER"
