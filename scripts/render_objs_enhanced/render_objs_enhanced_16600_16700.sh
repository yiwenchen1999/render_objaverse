#!/bin/bash
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --time=8:00:00
#SBATCH --job-name=render_models_dense_dist_16600_16700
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:1
#SBATCH --output=myjob.render_models_dense_dist_16600_16700.out
#SBATCH --error=myjob.render_models_dense_dist_16600_16700.err

cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

GROUP_START=16600
GROUP_END=16700
LIGHTING_SEED=$((2021 + GROUP_START))

python scripts/distribute_render_3dmodels_dense_enhance.py   --num_gpus 1   --workers_per_gpu 2   --group_start "${GROUP_START}"   --group_end "${GROUP_END}"   --num_views 30   --num_test_views 50   --dynamic_lighting_counts   --enable_combined   --combined_probability 0.20   --lighting_seed "${LIGHTING_SEED}"   --rho_min 0.3   --rho_max 1.1   --rendered_dir_name rendered_objs_enhanced   --csv_path test_obj.csv   --proj_root /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

echo "Done."
