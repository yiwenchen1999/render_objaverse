#!/bin/bash
# Quick test script to verify num_views and num_test_views parameters
# Run on Sony cluster to test a single scene

set -euo pipefail

PROJ="/music-shared-disk/group/ct/yiwen/codes/render_objaverse"
cd "$PROJ"

echo "========================================="
echo "Testing 3D scene rendering with custom views"
echo "========================================="

# Test with reduced views for quick validation
python3 SonyAIClusterUtil/distribute_render_3dscenes_sony.py \
  --num_gpus 1 \
  --workers_per_gpu 4 \
  --group_start 0 \
  --group_end 10 \
  --num_views 20 \
  --num_test_views 5 \
  --num_white_envs 1 \
  --num_env_lights 1 \
  --num_white_pls 1 \
  --num_rgb_pls 0 \
  --num_multi_pls 0 \
  --num_area_lights 0 \
  --num_combined_lights 1 \
  --model_lq_dir /music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_models \
  --output_dir /music-shared-disk/group/ct/yiwen/data/objaverse/test_rendered_scenes \
  --texture_dir /music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_textures \
  --env_map_dir /music-shared-disk/group/ct/yiwen/data/objaverse/hdris \
  --glb_list_path test_obj_curated.csv \
  --glbs_root_path /music-shared-disk/group/ct/yiwen/data/objaverse/objaverse/hf-objaverse-v1/glbs/ \
  --proj_root "$PROJ"

echo ""
echo "========================================="
echo "Test complete! Check output:"
echo "  ls /music-shared-disk/group/ct/yiwen/data/objaverse/test_rendered_scenes/"
echo "========================================="
