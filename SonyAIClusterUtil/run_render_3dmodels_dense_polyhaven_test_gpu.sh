#!/bin/bash
# =============================================================================
# Test run: render a few models with GPU usage monitoring.
# Use this to observe GPU utilization and tune --cycles_tile_size.
#
# Run on compute node (after sbash or srun):
#   bash SonyAIClusterUtil/run_render_3dmodels_dense_polyhaven_test_gpu.sh
#
# Or one-shot: srun --partition=ct --account=ct --gres=gpu:1 \
#   bash SonyAIClusterUtil/run_render_3dmodels_dense_polyhaven_test_gpu.sh
#
# Check slurm_logs/gpu_usage_*.csv after run for utilization stats.
# =============================================================================

set -euo pipefail

PROJ="${PROJ:-/music-shared-disk/group/ct/yiwen/codes/render_objaverse}"
BLENDER_BIN="${BLENDER_BIN:-${PROJ}/neuralGaufferRendering/blender-3.2.2-linux-x64/blender}"
[[ ! -x "$BLENDER_BIN" ]] && BLENDER_BIN="${PROJ}/neuralGaufferRendering/blender-4.2-linux-x64/blender"

mkdir -p slurm_logs
export SDL_AUDIODRIVER=dummy

# Test: 1 model (group 0-1), few views; large tile for H100
GROUP_START=11
GROUP_END=12
NUM_VIEWS=4
NUM_TEST_VIEWS=4
CYCLES_TILE=4096  # H100: try 2048, 4096 for higher GPU utilization

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJ"

GPU_LOG="slurm_logs/gpu_usage_test_$(date +%H%M%S).csv"
echo "=== GPU-monitored test run: group $GROUP_START-$GROUP_END, cycles_tile_size=$CYCLES_TILE ==="
echo "Log: $GPU_LOG"
echo ""

GPU_LOG_PATH="$GPU_LOG" bash "$SCRIPT_DIR/SonyAIClusterUtil/run_with_gpu_monitor.sh" -- \
  "$BLENDER_BIN" -b -P render_3dmodels_dense_polyhaven.py -- \
  --group_start $GROUP_START \
  --group_end $GROUP_END \
  --output_dir /music-shared-disk/group/ct/yiwen/data/objaverse/rendered_dense_polyhaven \
  --model_lq_dir /music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_models \
  --env_map_dir_path /music-shared-disk/group/ct/yiwen/data/objaverse/hdris \
  --white_env_map_dir_path /music-shared-disk/group/ct/yiwen/data/objaverse/hdris \
  --model_list_path assets/object_ids/polyhaven_models_train.json \
  --num_views $NUM_VIEWS \
  --num_test_views $NUM_TEST_VIEWS \
  --rendered_dir_name /music-shared-disk/group/ct/yiwen/data/objaverse/rendered_dense_polyhaven \
  --cycles_tile_size $CYCLES_TILE

echo "Done. Inspect slurm_logs/gpu_usage_*.csv for utilization."
