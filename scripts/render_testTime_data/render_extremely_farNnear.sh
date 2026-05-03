#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=60:00:00
#SBATCH --job-name=render_models_dense_dist_250_300
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:a5000:1
#SBATCH --output=myjob.render_models_dense_dist_250_300.out
#SBATCH --error=myjob.render_models_dense_dist_250_300.err
# =============================================================================
# Multi-worker distributed rendering: models 250-300 with 2 workers per GPU
# Submit: cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse && \
#   sbatch scripts/render_3dmodels_dense_250_300.sh
# =============================================================================

cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

run_batch () {
  local min_dist=$1
  local max_dist=$2
  local out_dir=$3
  local dataset_root=/projects/vig/Datasets/objaverse/hf-objaverse-v1

  echo "Running batch: ${out_dir} (min_dist=${min_dist}, max_dist=${max_dist})"
  mkdir -p "${dataset_root}/${out_dir}"
  python scripts/distribute_render_3dmodels_addLights.py \
    --num_gpus 1 \
    --workers_per_gpu 2 \
    --group_start 13250 \
    --group_end 13252 \
    --num_views 4 \
    --num_test_views 50 \
    --test_min_dist_to_origin "${min_dist}" \
    --test_max_dist_to_origin "${max_dist}" \
    --num_white_envs 0 \
    --num_env_lights 1 \
    --num_white_pls 0 \
    --num_rgb_pls 0 \
    --num_multi_pls 0 \
    --num_area_lights 0 \
    --num_combined_lights 0 \
    --rendered_dir_name "${out_dir}" \
    --csv_path test_obj.csv \
    --proj_root /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse
}

# Near test set: trajectory radius = 0.6
run_batch 0.6 0.6 rendered_dense_robustTest_near

# Normal test set: trajectory radius = 1.0
run_batch 1.0 1.0 rendered_dense_robustTest_normal

# Far test set: trajectory radius = 5.0
run_batch 5.0 5.0 rendered_dense_robustTest_far

echo "Done."
