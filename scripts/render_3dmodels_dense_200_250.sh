#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=60:00:00
#SBATCH --job-name=render_objaverse_addLights_10400_10500
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:a5000:1
#SBATCH --output=myjob.render_objaverse_addLights_10400_10500.out
#SBATCH --error=myjob.render_objaverse_addLights_10400_10500.err

# python ../download.py --base_path /projects/vig/Datasets --begin_uid 200 --end_uid 250
python render_3dmodels_dense_addLights.py --group_start 10400 --group_end 10500 \
--num_views 30 --num_env_lights 0 --num_white_envs 0 --num_test_views 50 \
--num_white_pls 3 --num_rgb_pls 1 --num_multi_pls 0 --save_intrinsics True \
--num_area_lights 0 --rendered_dir_name rendered_dense_lightPlus
