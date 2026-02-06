#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=48:00:00
#SBATCH --job-name=download_objaverse
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --output=myjob.download_objaverse.out
#SBATCH --error=myjob.download_objaverse.err

python download.py --obj_list test_obj.csv --end_uid 8000
