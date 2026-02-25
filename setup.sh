cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse
conda activate /projects/vig/yiwenc/all_env/blender-env

find -maxdepth 1 -type d | sort | while read -r dir; do n=$(find "$dir" -type f | wc -l); printf "%4d : %s\n" $n "$dir"; done

python3 scripts/sample_test_obj.py

cd /Users/yiwenchen/Desktop/ResearchProjects/scripts
source venv/bin/activate

python render_previews_lvis.py \
    --csv_path ./test_obj.csv \
    --group_start 2000 \
    --group_end 5000 \
    --output_dir /projects/vig/Datasets/objaverse/hf-objaverse-v1/glb_previews_2000-5000

srun --partition=gpu --nodes=1 --pty --gres=gpu:1 --ntasks=8 --mem=32 --time=8:00:00 /bin/bash

python render_3dscenes_dense.py \
    --group_start 19 \
    --group_end 20 \
    --num_white_envs 1 \
    --num_env_lights 0 \
    --model_lq_dir /projects/vig/Datasets/Polyhaven/polyhaven_models \
    --output_dir ./output_scenes_dense
