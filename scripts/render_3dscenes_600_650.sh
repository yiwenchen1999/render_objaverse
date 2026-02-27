#!/bin/bash
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --time=8:00:00
#SBATCH --job-name=render_scenes_dist_5600_5650
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:1
#SBATCH --output=myjob.render_scenes_dist_5600_5650.out
#SBATCH --error=myjob.render_scenes_dist_5600_5650.err
# =============================================================================
# Multi-worker distributed rendering: scenes 5600-5650 with 2 workers per GPU
# Submit: cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse && \
#   sbatch scripts/render_3dscenes_600_650.sh
# =============================================================================

cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

python scripts/distribute_render_3dscenes.py \
  --num_gpus 1 \
  --workers_per_gpu 2 \
  --group_start 5600 \
  --group_end 5650 \
  --num_white_envs 1 \
  --num_env_lights 3 \
  --num_white_pls 3 \
  --num_rgb_pls 1 \
  --num_multi_pls 0 \
  --num_area_lights 0 \
  --model_lq_dir /projects/vig/Datasets/Polyhaven/polyhaven_models \
  --output_dir ./output_scenes_dense \
  --texture_dir /projects/vig/Datasets/Polyhaven/polyhaven_textures \
  --glb_list_path test_obj_curated.csv \
  --glbs_root_path /projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/ \
  --proj_root /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

echo "Done."
