#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=24:00:00
#SBATCH --job-name=render_objaverse_150_200
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gpus=1
#SBATCH --gres=gpu:a5000:1
#SBATCH --output=myjob.render_objaverse_150_200.out
#SBATCH --error=myjob.render_objaverse_150_200.err

# python ../download.py --base_path /projects/vig/Datasets --begin_uid 150 --end_uid 200
python render_3dmodels_dense.py --group_start 150 --group_end 200
