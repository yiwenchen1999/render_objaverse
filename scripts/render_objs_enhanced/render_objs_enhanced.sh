#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=60:00:00
#SBATCH --job-name=render_models_dense_dist_0_50
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:a5000:1
#SBATCH --output=myjob.render_models_dense_dist_0_50.out
#SBATCH --error=myjob.render_models_dense_dist_0_50.err
# =============================================================================
# Multi-worker distributed rendering: models 0-50 with 2 workers per GPU
# Submit: cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse && \
#   sbatch scripts/render_3dmodels_dense_0_50.sh
# =============================================================================

cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

python scripts/distribute_render_3dmodels_dense_enhance.py \
  --num_gpus 1 \
  --workers_per_gpu 2 \
  --group_start 18200 \
  --group_end 18250 \
  --num_views 1 \
  --num_test_views 1 \
  --dynamic_lighting_counts \
  --enable_combined \
  --combined_probability 0.25 \
  --lighting_seed 2022 \
  --rendered_dir_name rendered_objs_enhanced \
  --csv_path test_obj.csv \
  --proj_root /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

echo "Done."
