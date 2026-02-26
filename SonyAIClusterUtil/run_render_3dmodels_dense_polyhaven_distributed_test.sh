#!/bin/bash
# =============================================================================
# Interactive test: render a few models with 4 workers per GPU
# Run on compute node (after sbash or srun):
#   bash SonyAIClusterUtil/run_render_3dmodels_dense_polyhaven_distributed_test.sh
# =============================================================================

set -euo pipefail

PROJ="${PROJ:-/music-shared-disk/group/ct/yiwen/codes/render_objaverse}"
cd "$PROJ"

export SDL_AUDIODRIVER=dummy
mkdir -p slurm_logs

# Test: 4 models, 4 workers per GPU
python3 SonyAIClusterUtil/distribute_render_polyhaven.py \
  --num_gpus 1 \
  --workers_per_gpu 8 \
  --group_start 20 \
  --group_end 36 \
  --model_list_path assets/object_ids/polyhaven_models_train.json \
  --output_dir /music-shared-disk/group/ct/yiwen/data/objaverse/rendered_dense_polyhaven \
  --model_lq_dir /music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_models \
  --env_map_dir /music-shared-disk/group/ct/yiwen/data/objaverse/hdris \
  --num_views 4 \
  --num_test_views 4 \
  --cycles_tile_size 512 \
  --proj_root "$PROJ"

echo "Done. Check GPU usage with: nvidia-smi dmon -s u"
