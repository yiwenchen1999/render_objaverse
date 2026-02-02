#!/bin/bash
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --time=8:00:00
#SBATCH --job-name=render_objaverse_4600-4650
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:1
#SBATCH --output=myjob.render_objaverse_4600-4650.out
#SBATCH --error=myjob.render_objaverse_4600-4650.err

# python ../download.py --base_path /projects/vig/Datasets --begin_uid 600 --end_uid 650
python render_3dmodels_dense.py --group_start 4600 --group_end 4650 \
--num_views 30 --num_env_lights 3 --num_test_views 50 \
--num_white_pls 0 --num_rgb_pls 0 --num_multi_pls 0 \
--num_area_lights 0 --rendered_dir_name rendered_dense_lightPlus

