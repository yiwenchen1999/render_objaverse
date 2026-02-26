#!/bin/bash
# =============================================================================
# Sony cluster: interactive run for render_3dmodels_dense_polyhaven.py
# Usage:
#   ssh mfml1
#   cd /music-shared-disk/group/ct/yiwen/codes/render_objaverse
#   bash SonyAIClusterUtil/run_render_3dmodels_dense_polyhaven_interactive.sh
#
# Override via environment (optional):
#   PROJ BLENDER_BIN GROUP_START GROUP_END OUTPUT_DIR MODEL_LQ_DIR
#   ENV_MAP_DIR MODEL_LIST_PATH NUM_VIEWS NUM_TEST_VIEWS
#
# Prereq: Blender installed in PROJ (4.2 or neuralGaufferRendering 3.2.2).
#         Blender's Python must have: pip install simple_parsing imageio
#         (e.g. ./blender-4.2-linux-x64/4.2/python/bin/python3 -m pip install ...)
# =============================================================================

set -euo pipefail

# Project and Blender
PROJ="${PROJ:-/music-shared-disk/group/ct/yiwen/codes/render_objaverse}"
BLENDER_BIN="${BLENDER_BIN:-${PROJ}/blender-4.2-linux-x64/blender}"
# Fallback to neuralGauffer Blender 3.2 if 4.2 not present
if [[ ! -x "$BLENDER_BIN" ]]; then
  BLENDER_BIN="${PROJ}/neuralGaufferRendering/blender-3.2.2-linux-x64/blender"
fi
if [[ ! -x "$BLENDER_BIN" ]]; then
  echo "Error: Blender not found. Set BLENDER_BIN or install Blender in project."
  exit 1
fi

# Slurm
PARTITION="${PARTITION:-ct}"
ACCOUNT="${ACCOUNT:-ct}"
GPU="${GPU:-1}"

# Render range and paths
GROUP_START="${GROUP_START:-0}"
GROUP_END="${GROUP_END:-1}"
OUTPUT_DIR="${OUTPUT_DIR:-/music-shared-disk/group/ct/yiwen/data/objaverse/rendered_dense_polyhaven}"
MODEL_LQ_DIR="${MODEL_LQ_DIR:-/music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_models}"
ENV_MAP_DIR="${ENV_MAP_DIR:-/music-shared-disk/group/ct/yiwen/data/objaverse/hdris}"
MODEL_LIST_PATH="${MODEL_LIST_PATH:-assets/object_ids/polyhaven_models_train.json}"
NUM_VIEWS="${NUM_VIEWS:-4}"
NUM_TEST_VIEWS="${NUM_TEST_VIEWS:-4}"

echo "=============================================="
echo "Interactive: render_3dmodels_dense_polyhaven"
echo "=============================================="
echo "PROJ=$PROJ"
echo "BLENDER_BIN=$BLENDER_BIN"
echo "GROUP_START=$GROUP_START GROUP_END=$GROUP_END"
echo "OUTPUT_DIR=$OUTPUT_DIR"
echo "PARTITION=$PARTITION ACCOUNT=$ACCOUNT gpus=$GPU"
echo "=============================================="

cd "$PROJ"

srun --partition="$PARTITION" --account="$ACCOUNT" --gres=gpu:"$GPU" --job-name=bpy_polyhaven \
  bash -lc "
    set -e
    cd $PROJ
    $BLENDER_BIN -b -P render_3dmodels_dense_polyhaven.py -- \
      --group_start $GROUP_START \
      --group_end $GROUP_END \
      --output_dir $OUTPUT_DIR \
      --model_lq_dir $MODEL_LQ_DIR \
      --env_map_dir_path $ENV_MAP_DIR \
      --white_env_map_dir_path $ENV_MAP_DIR \
      --model_list_path $MODEL_LIST_PATH \
      --num_views $NUM_VIEWS \
      --num_test_views $NUM_TEST_VIEWS \
      --rendered_dir_name rendered_dense_polyhaven
  "

echo "Done."
