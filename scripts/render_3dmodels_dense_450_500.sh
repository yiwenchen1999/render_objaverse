#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=60:00:00
#SBATCH --job-name=render_models_dense_dist_450_500
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:a5000:1
#SBATCH --output=myjob.render_models_dense_dist_450_500.out
#SBATCH --error=myjob.render_models_dense_dist_450_500.err
# =============================================================================
# Multi-worker distributed rendering: models 450-500 with 2 workers per GPU
# Submit: cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse && \
#   sbatch scripts/render_3dmodels_dense_450_500.sh
# =============================================================================

cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

python scripts/distribute_render_3dmodels_addLights.py \
  --num_gpus 1 \
  --workers_per_gpu 2 \
  --group_start 7450 \
  --group_end 7500 \
  --num_views 30 \
  --num_test_views 50 \
  --num_white_envs 1 \
  --num_env_lights 0 \
  --num_white_pls 1 \
  --num_rgb_pls 1 \
  --num_multi_pls 1 \
  --num_area_lights 1 \
  --num_combined_lights 4 \
  --rendered_dir_name rendered_dense_lightPlus \
  --csv_path test_obj.csv \
  --proj_root /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

echo "Done."
