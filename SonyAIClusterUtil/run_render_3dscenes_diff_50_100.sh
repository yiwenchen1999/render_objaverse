#!/bin/bash
#SBATCH --partition=sharedp
#SBATCH --account=ct
#SBATCH --requeue
#SBATCH --job-name=render_scenes_diff_0_50
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:2
#SBATCH --output=slurm_logs/%x.%j.out
#SBATCH --error=slurm_logs/%x.%j.err
# =============================================================================
# Multi-worker distributed rendering: 3D scenes 0-50 with 4 workers per GPU
# Submit: cd /music-shared-disk/group/ct/yiwen/codes/render_objaverse && \
#   sbatch SonyAIClusterUtil/run_render_3dscenes_diff_0_50.sh
# =============================================================================

set -euo pipefail

mkdir -p slurm_logs
export SDL_AUDIODRIVER=dummy

PROJ="/music-shared-disk/group/ct/yiwen/codes/render_objaverse"
cd "$PROJ"

# Multi-worker: Blender processes per GPU (runs render_3dscenes_dense_diff.py)
python3 SonyAIClusterUtil/distribute_render_3dscenes_diff_sony.py \
  --num_gpus 2 \
  --workers_per_gpu 6 \
  --group_start 10000 \
  --group_end 10050 \
  --num_views 12 \
  --num_test_views 50 \
  --num_white_envs 1 \
  --num_env_lights 10 \
  --num_white_pls 10 \
  --num_rgb_pls 0 \
  --num_multi_pls 0 \
  --num_area_lights 0 \
  --num_combined_lights 4 \
  --model_lq_dir /music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_models \
  --output_dir /music-shared-disk/group/ct/yiwen/data/objaverse/rendered_scenes_diff \
  --texture_dir /music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_textures \
  --env_map_dir /music-shared-disk/group/ct/yiwen/data/objaverse/hdris \
  --glb_list_path test_obj_curated.csv \
  --glbs_root_path /music-shared-disk/group/ct/yiwen/data/objaverse/objaverse/hf-objaverse-v1/glbs/ \
  --proj_root "$PROJ"

echo "Done."
