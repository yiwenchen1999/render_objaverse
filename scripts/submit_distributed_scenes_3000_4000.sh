#!/bin/bash
# =============================================================================
# Submit all distributed scene rendering jobs for range 3000-4000
# Usage: bash scripts/submit_distributed_scenes_3000_4000.sh
# =============================================================================

set -euo pipefail

cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

# Check if distributed scripts exist
if [ ! -f scripts/distribute_render_3dscenes_3000_3125.sh ]; then
  echo "Error: Distributed scripts (3000-4000) not found."
  echo "Run: bash scripts/generate_distributed_scripts_3000_4000.sh"
  exit 1
fi

# Submit all jobs in 3000-4000 range
echo "Submitting distributed scene rendering jobs (3000-4000, 8 jobs)"
echo ""

for script in scripts/distribute_render_3dscenes_3*.sh; do
  echo "Submitting: $script"
  sbatch "$script"
  sleep 1
done

echo ""
echo "All jobs (3000-4000) submitted!"
echo "Check status: squeue -u \$USER"
