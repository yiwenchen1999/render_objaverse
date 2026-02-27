#!/bin/bash
#SBATCH --partition=sharedp
#SBATCH --account=ct
#SBATCH --requeue
#SBATCH --job-name=bpy_ph_dist_60_120
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --output=slurm_logs/%x.%j.out
#SBATCH --error=slurm_logs/%x.%j.err
# =============================================================================
# Multi-worker dispatcher: render group 60-120 with 4 workers per GPU
# Submit: cd /music-shared-disk/group/ct/yiwen/codes/render_objaverse && \
#   sbatch SonyAIClusterUtil/run_render_3dmodels_dense_polyhaven_distributed_60_120.sh
# =============================================================================

set -euo pipefail

mkdir -p slurm_logs
export SDL_AUDIODRIVER=dummy

PROJ="/music-shared-disk/group/ct/yiwen/codes/render_objaverse"
cd "$PROJ"

# Multi-worker: 4 Blender processes per GPU
python3 SonyAIClusterUtil/distribute_render_polyhaven.py \
  --num_gpus 1 \
  --workers_per_gpu 6 \
  --group_start 60 \
  --group_end 120 \
  --model_list_path assets/object_ids/polyhaven_models_train.json \
  --output_dir /music-shared-disk/group/ct/yiwen/data/objaverse/rendered_dense_polyhaven \
  --model_lq_dir /music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_models \
  --env_map_dir /music-shared-disk/group/ct/yiwen/data/objaverse/hdris \
  --num_views 30 \
  --num_test_views 100 \
  --cycles_tile_size 512 \
  --proj_root "$PROJ"

echo "Done."
