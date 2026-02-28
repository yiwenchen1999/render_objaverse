#!/bin/bash
# Submit all 3D scene rendering jobs to Sony cluster
# Covers scenes 0-2302

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "========================================"
echo "Submitting all 3D scene rendering jobs"
echo "========================================"

# Submit all scripts
for script in SonyAIClusterUtil/run_render_3dscenes_distributed_*.sh; do
  if [[ -f "$script" ]]; then
    echo "Submitting: $script"
    sbatch "$script"
    sleep 0.5  # Small delay to avoid overwhelming scheduler
  fi
done

echo ""
echo "✅ All jobs submitted!"
echo ""
echo "Check status:"
echo "  squeue -u \$USER"
echo ""
echo "Monitor output:"
echo "  tail -f slurm_logs/render_scenes_*.out"
