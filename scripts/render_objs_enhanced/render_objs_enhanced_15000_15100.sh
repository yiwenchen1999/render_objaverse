#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=60:00:00
#SBATCH --job-name=render_models_dense_dist_15000_15100
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:a5000:1
#SBATCH --output=myjob.render_models_dense_dist_15000_15100.out
#SBATCH --error=myjob.render_models_dense_dist_15000_15100.err
# =============================================================================
# Multi-worker distributed rendering: models 15000-15100 with 2 workers per GPU
# Submit: cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse && \
#   sbatch scripts/render_objs_enhanced/render_objs_enhanced_15000_15100.sh
# =============================================================================

cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

GROUP_START=15000
GROUP_END=15100
LIGHTING_SEED=$((2021 + GROUP_START))

python scripts/distribute_render_3dmodels_dense_enhance.py \
  --num_gpus 1 \
  --workers_per_gpu 2 \
  --group_start "${GROUP_START}" \
  --group_end "${GROUP_END}" \
  --num_views 30 \
  --num_test_views 50 \
  --dynamic_lighting_counts \
  --enable_combined \
  --combined_probability 0.20 \
  --lighting_seed "${LIGHTING_SEED}" \
  --rho_min 0.3 \
  --rho_max 1.1 \
  --rendered_dir_name rendered_objs_enhanced \
  --csv_path test_obj.csv \
  --proj_root /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

echo "Done."
