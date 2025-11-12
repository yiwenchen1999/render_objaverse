#!/bin/bash
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --time=8:00:00
#SBATCH --job-name=render_objaverse_350_400
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:1
#SBATCH --output=myjob.render_objaverse_350_400.out
#SBATCH --error=myjob.render_objaverse_350_400.err

# python ../download.py --base_path /projects/vig/Datasets --begin_uid 350 --end_uid 400
python render_3dmodels_dense.py --group_start 350 --group_end 400
