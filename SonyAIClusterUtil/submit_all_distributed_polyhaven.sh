#!/bin/bash
# =============================================================================
# Submit all distributed Polyhaven rendering jobs (4 groups: 0-240)
# Usage: bash SonyAIClusterUtil/submit_all_distributed_polyhaven.sh
# =============================================================================

set -euo pipefail

cd /music-shared-disk/group/ct/yiwen/codes/render_objaverse

echo "Submitting all distributed Polyhaven rendering jobs (0-240, 4 jobs x 60 models each)"
echo ""

for script in SonyAIClusterUtil/run_render_3dmodels_dense_polyhaven_distributed_*.sh; do
  if [[ "$script" != *"test"* ]]; then
    echo "Submitting: $script"
    sbatch "$script"
    sleep 1
  fi
done

echo ""
echo "All jobs submitted!"
echo "Check status: squeue -u \$USER"
echo "Monitor logs: tail -f slurm_logs/bpy_ph_dist_*.out"
