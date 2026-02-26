#!/bin/bash
# Submit all 4 sharedp jobs for render_3dmodels_dense_polyhaven (groups 0-240, 60 items each).
# Run from project root: bash SonyAIClusterUtil/submit_render_polyhaven_0_240.sh

set -euo pipefail

cd "$(dirname "$0")/.."
echo "Submitting render_3dmodels_dense_polyhaven sharedp jobs (0-60, 60-120, 120-180, 180-240)..."
sbatch SonyAIClusterUtil/run_render_3dmodels_dense_polyhaven_sbatch_0_60.sh
sbatch SonyAIClusterUtil/run_render_3dmodels_dense_polyhaven_sbatch_60_120.sh
sbatch SonyAIClusterUtil/run_render_3dmodels_dense_polyhaven_sbatch_120_180.sh
sbatch SonyAIClusterUtil/run_render_3dmodels_dense_polyhaven_sbatch_180_240.sh
echo "Done. Check: squeue -u \$USER"
