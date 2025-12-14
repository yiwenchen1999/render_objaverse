#!/bin/bash
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --time=8:00:00
#SBATCH --job-name=render_objaverse_100_150
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:h200:1
#SBATCH --output=myjob.render_objaverse_100_150.out
#SBATCH --error=myjob.render_objaverse_100_150.err

# python ../download.py --base_path /projects/vig/Datasets --begin_uid 100 --end_uid 150
python render_3dmodels_dense.py --group_start 100 --group_end 150
