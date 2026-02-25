#!/bin/bash
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --time=8:00:00
#SBATCH --job-name=render_3dscenes_700_750
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:1
#SBATCH --output=myjob.render_3dscenes_700_750.out
#SBATCH --error=myjob.render_3dscenes_700_750.err

python render_3dscenes_dense.py \
    --group_start 700 --group_end 750 \
    --num_white_envs 1 --num_env_lights 3 \
    --model_lq_dir /projects/vig/Datasets/Polyhaven/polyhaven_models \
    --output_dir ./output_scenes_dense