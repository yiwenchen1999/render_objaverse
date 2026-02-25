#!/bin/bash
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --time=8:00:00
#SBATCH --job-name=render_3dscenes_850_900
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:1
#SBATCH --output=myjob.render_3dscenes_850_900.out
#SBATCH --error=myjob.render_3dscenes_850_900.err

python render_3dscenes_dense.py \
    --group_start 1850 --group_end 1900 \
    --num_views 30 --num_test_views 50 \
    --num_white_pls 3 --num_rgb_pls 1 --num_multi_pls 0 \
    --num_white_envs 1 --num_env_lights 3 \
    --model_lq_dir /projects/vig/Datasets/Polyhaven/polyhaven_models \
    --output_dir ./output_scenes_dense