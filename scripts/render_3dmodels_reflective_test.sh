#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=60:00:00
#SBATCH --job-name=render_objaverse_reflective_test
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:a5000:1
#SBATCH --output=myjob.render_objaverse_reflective_test.out
#SBATCH --error=myjob.render_objaverse_reflective_test.err

# Test script for reflective-material variation.
cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

python render_3dmodels_dense_reflective.py --group_start 8980 --group_end 9000 \
--num_views 3 --num_env_lights 3 --num_test_views 50 \
--num_env_lights 1 --num_white_pls 0 --num_rgb_pls 0 --num_multi_pls 0 \
--num_area_lights 0 --num_combined_lights 0 \
--rendered_dir_name rendered_dense_reflective \
--csv_path test_obj.csv
