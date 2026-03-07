#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=60:00:00
#SBATCH --job-name=render_scenes_dist_5950_6000
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:a5000:1
#SBATCH --output=myjob.render_scenes_dist_5950_6000.out
#SBATCH --error=myjob.render_scenes_dist_5950_6000.err
# =============================================================================
# Multi-worker distributed rendering: scenes 5950-6000 with 2 workers per GPU
# Submit: cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse && \
#   sbatch scripts/render_3dscenes_950_1000.sh
# =============================================================================

cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

python scripts/distribute_render_3dscenes.py \
  --num_gpus 1 \
  --workers_per_gpu 2 \
  --group_start 8950 \
  --group_end 9000 \
  --num_white_envs 1 \
  --num_env_lights 1 \
  --num_white_pls 1 \
  --num_rgb_pls 1 \
  --num_multi_pls 1 \
  --num_area_lights 1 \
  --num_combined_lights 4 \
  --model_lq_dir /projects/vig/Datasets/Polyhaven/polyhaven_models \
  --output_dir /projects/vig/Datasets/objaverse/hf-objaverse-v1/rendered_scenes_dense_expanded \
  --texture_dir /projects/vig/Datasets/Polyhaven/polyhaven_textures \
  --glb_list_path test_obj_curated.csv \
  --glbs_root_path /projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/ \
  --proj_root /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

echo "Done."
