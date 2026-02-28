#!/bin/bash
#SBATCH --partition=sharedp
#SBATCH --account=ct
#SBATCH --requeue
#SBATCH --job-name=render_scenes_1650_1700
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --output=slurm_logs/%x.%j.out
#SBATCH --error=slurm_logs/%x.%j.err
# =============================================================================
# Multi-worker distributed rendering: 3D scenes 1650-1700 with 4 workers per GPU
# Submit: cd /music-shared-disk/group/ct/yiwen/codes/render_objaverse && \
#   sbatch SonyAIClusterUtil/run_render_3dscenes_distributed_1650_1700.sh
# =============================================================================

set -euo pipefail

mkdir -p slurm_logs
export SDL_AUDIODRIVER=dummy

PROJ="/music-shared-disk/group/ct/yiwen/codes/render_objaverse"
cd "$PROJ"

# Multi-worker: 4 Blender processes per GPU
python3 SonyAIClusterUtil/distribute_render_3dscenes_sony.py \
  --num_gpus 1 \
  --workers_per_gpu 4 \
  --group_start 1650 \
  --group_end 1700 \
  --num_views 30 \
  --num_test_views 50 \
  --num_white_envs 1 \
  --num_env_lights 3 \
  --num_white_pls 3 \
  --num_rgb_pls 1 \
  --num_multi_pls 0 \
  --num_area_lights 0 \
  --model_lq_dir /music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_models \
  --output_dir /music-shared-disk/group/ct/yiwen/data/objaverse/rendered_scenes_dense \
  --texture_dir /music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_textures \
  --env_map_dir /music-shared-disk/group/ct/yiwen/data/objaverse/hdris \
  --glb_list_path test_obj_curated.csv \
  --glbs_root_path /music-shared-disk/group/ct/yiwen/data/objaverse/objaverse/hf-objaverse-v1/glbs/ \
  --proj_root "$PROJ"

echo "Done."
