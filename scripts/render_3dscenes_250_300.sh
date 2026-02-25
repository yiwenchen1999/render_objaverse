#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=60:00:00
#SBATCH --job-name=render_3dscenes_250_300
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:a5000:1
#SBATCH --output=myjob.render_3dscenes_250_300.out
#SBATCH --error=myjob.render_3dscenes_250_300.err

python render_3dscenes_dense.py \
    --group_start 250 --group_end 300 \
    --num_white_envs 1 --num_env_lights 3 \
    --model_lq_dir /projects/vig/Datasets/Polyhaven/polyhaven_models \
    --output_dir ./output_scenes_dense