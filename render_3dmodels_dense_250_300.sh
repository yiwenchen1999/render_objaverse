#!/bin/bash
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --time=8:00:00
#SBATCH --job-name=render_objaverse_250_300
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:a5000:1
#SBATCH --output=myjob.render_objaverse_250_300.out
#SBATCH --error=myjob.render_objaverse_250_300.err

# python ../download.py --base_path /projects/vig/Datasets --begin_uid 250 --end_uid 300
python render_3dmodels_dense.py --group_start 250 --group_end 300
