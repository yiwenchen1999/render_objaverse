cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse
conda activate /projects/vig/yiwenc/all_env/blender-env

find -maxdepth 1 -type d | sort | while read -r dir; do n=$(find "$dir" -type f | wc -l); printf "%4d : %s\n" $n "$dir"; done

python3 scripts/sample_test_obj.py

cd /Users/yiwenchen/Desktop/ResearchProjects/scripts
source venv/bin/activate

srun --partition=gpu --nodes=1 --pty --gres=gpu:1 --ntasks=8 --mem=32 --time=8:00:00 /bin/bash

python render_3dscenes_dense.py \
    --group_start 0 \
    --group_end 1 \
    --num_white_envs 1 \
    --num_env_lights 0 \
    --output_dir ./output_scenes_dense