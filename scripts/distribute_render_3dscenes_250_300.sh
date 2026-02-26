#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=60:00:00
#SBATCH --job-name=render_scenes_dist_3250_3300
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:a5000:1
#SBATCH --output=myjob.render_scenes_dist_3250_3300.out
#SBATCH --error=myjob.render_scenes_dist_3250_3300.err
# =============================================================================
# Multi-worker distributed rendering: scenes 3250-3300 with 4 workers per GPU
# Submit: cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse && \
#   sbatch scripts/distribute_render_3dscenes_250_300.sh
# Prerequisite: conda activate blender-env (before submitting)
# =============================================================================

cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

python scripts/distribute_render_3dscenes.py \
  --num_gpus 1 \
  --workers_per_gpu 4 \
  --group_start 3250 \
  --group_end 3300 \
  --num_white_envs 1 \
  --num_env_lights 3 \
  --num_white_pls 0 \
  --num_rgb_pls 0 \
  --num_multi_pls 0 \
  --num_area_lights 0 \
  --model_lq_dir /projects/vig/Datasets/Polyhaven/polyhaven_models \
  --output_dir ./output_scenes_dense \
  --texture_dir /projects/vig/Datasets/Polyhaven/polyhaven_textures \
  --glb_list_path test_obj_curated.csv \
  --glbs_root_path /projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/ \
  --num_white_pls 0 \
  --num_rgb_pls 0 \
  --num_multi_pls 0 \
  --num_area_lights 0 \
  --proj_root /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

echo "Done."
