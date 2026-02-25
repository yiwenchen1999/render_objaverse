#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=60:00:00
#SBATCH --job-name=render_3dscenes_300_350
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:a5000:1
#SBATCH --output=myjob.render_3dscenes_300_350.out
#SBATCH --error=myjob.render_3dscenes_300_350.err

python render_3dscenes_dense.py \
    --group_start 300 --group_end 350 \
    --num_white_envs 1 --num_env_lights 3 \
    --model_lq_dir /projects/vig/Datasets/Polyhaven/polyhaven_models \
    --output_dir ./output_scenes_dense