#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=60:00:00
#SBATCH --job-name=render_objaverse_grazingLight_test
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:a5000:1
#SBATCH --output=myjob.render_objaverse_grazingLight_test.out
#SBATCH --error=myjob.render_objaverse_grazingLight_test.err

# Test script for grazing-angle point-light variation.
cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

python render_3dmodels_dense_grazingLight.py --group_start 8000 --group_end 8050 \
--num_views 3 --num_env_lights 0 --num_test_views 50 \
--num_white_envs 1 --num_white_pls 1 --num_rgb_pls 0 --num_multi_pls 0 \
--num_area_lights 0 --num_combined_lights 0 \
--rendered_dir_name rendered_dense_grazingLight \
--csv_path test_obj.csv
