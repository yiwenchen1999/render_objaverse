#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=48:00:00
#SBATCH --job-name=render_objaverse4000to5000
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gpus=1
#SBATCH --output=myjob.render_objaverse4000to5000.out
#SBATCH --error=myjob.render_objaverse4000to5000.err

python ../download.py --base_path /projects/vig/Datasets --begin_uid 4000 --end_uid 5000
python render_3dmodels_explorer.py --group_start 4000 --group_end 5000


