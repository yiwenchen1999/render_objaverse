#!/bin/bash
#SBATCH --partition=short
#SBATCH --nodes=1
#SBATCH --time=24:00:00
#SBATCH --job-name=render_objaverse_700-750
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --output=myjob.render_objaverse_700-750.out
#SBATCH --error=myjob.render_objaverse_700-750.err

# python ../download.py --base_path /projects/vig/Datasets --begin_uid 650 --end_uid 700
python render_3dmodels_dense.py --group_start 1700 --group_end 1750 \
--num_views 30 --num_env_lights 3 --num_test_views 50 \
--num_white_pls 0 --num_rgb_pls 0 --num_multi_pls 0 \
--num_area_lights 0 --rendered_dir_name rendered_dense_lightPlus

