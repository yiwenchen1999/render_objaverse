#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=24:00:00
#SBATCH --job-name=render_objaverse_400_450
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:a5000:1
#SBATCH --output=myjob.render_objaverse_400_450.out
#SBATCH --error=myjob.render_objaverse_400_450.err

# python ../download.py --base_path /projects/vig/Datasets --begin_uid 400 --end_uid 450
python render_3dmodels_dense.py --group_start 900 --group_end 950 \
--num_views 30 --num_env_lights 3 --num_test_views 50 \
--num_white_pls 2 --num_rgb_pls 2 --num_multi_pls 2 \
--num_area_lights 3 --rendered_dir_name rendered_dense_lightPlus
