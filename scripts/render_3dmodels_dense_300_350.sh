#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=8:00:00
#SBATCH --job-name=render_objaverse_300_350
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:a5000:1
#SBATCH --output=myjob.render_objaverse_300_350.out
#SBATCH --error=myjob.render_objaverse_300_350.err

# python ../download.py --base_path /projects/vig/Datasets --begin_uid 300 --end_uid 350
python render_3dmodels_dense.py --group_start 300 --group_end 350
