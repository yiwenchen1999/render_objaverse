#!/bin/bash
# =============================================================================
# Sony cluster: interactive run for render_3dmodels_dense_polyhaven.py
# Reference: shortcuts.sh, sonyai_crusoe_day1_quickstart.md (sbash / srun)
#
# --- Option A: Interactive shell (sbash) ---
#   ssh mfml1
#   sbash --partition=ct --account=ct --nodes=1 --gpus=1
#   # once on compute node, run the commands printed by this script with:
#   bash SonyAIClusterUtil/run_render_3dmodels_dense_polyhaven_interactive.sh run_on_node
#
# --- Option B: One-shot srun (foreground, same style as shortcuts.sh) ---
#   ssh mfml1
#   cd /music-shared-disk/group/ct/yiwen/codes/render_objaverse
#   bash SonyAIClusterUtil/run_render_3dmodels_dense_polyhaven_interactive.sh
#
# Override via environment: PROJ BLENDER_BIN GROUP_START GROUP_END OUTPUT_DIR
#   MODEL_LQ_DIR ENV_MAP_DIR MODEL_LIST_PATH NUM_VIEWS NUM_TEST_VIEWS
# Prereq: Run once to install deps into Blender's Python:
#   bash SonyAIClusterUtil/install_blender_python_deps.sh
# =============================================================================

set -euo pipefail

PROJ="${PROJ:-/music-shared-disk/group/ct/yiwen/codes/render_objaverse}"
BLENDER_BIN="${BLENDER_BIN:-${PROJ}/neuralGaufferRendering/blender-3.2.2-linux-x64/blender}"
if [[ ! -x "$BLENDER_BIN" ]]; then
  BLENDER_BIN="${PROJ}/neuralGaufferRendering/blender-4.2-linux-x64/blender"
fi
if [[ ! -x "$BLENDER_BIN" ]]; then
  echo "Error: Blender not found. Set BLENDER_BIN or install Blender in project."
  exit 1
fi

PARTITION="${PARTITION:-ct}"
ACCOUNT="${ACCOUNT:-ct}"
GROUP_START="${GROUP_START:-0}"
GROUP_END="${GROUP_END:-10}"
OUTPUT_DIR="${OUTPUT_DIR:-/scratch2/$USER/rendered_dense_polyhaven}"
MODEL_LQ_DIR="${MODEL_LQ_DIR:-/music-shared-disk/group/ct/yiwen/data/Polyhaven/polyhaven_models}"
ENV_MAP_DIR="${ENV_MAP_DIR:-/music-shared-disk/group/ct/yiwen/data/envmaps/hdris}"
MODEL_LIST_PATH="${MODEL_LIST_PATH:-assets/object_ids/polyhaven_models_train.json}"
NUM_VIEWS="${NUM_VIEWS:-4}"
NUM_TEST_VIEWS="${NUM_TEST_VIEWS:-4}"

# Commands to run on the compute node (for sbash workflow)
run_on_node() {
  cd "$PROJ"
  "$BLENDER_BIN" -b -P render_3dmodels_dense_polyhaven.py -- \
    --group_start "$GROUP_START" \
    --group_end "$GROUP_END" \
    --output_dir "$OUTPUT_DIR" \
    --model_lq_dir "$MODEL_LQ_DIR" \
    --env_map_dir_path "$ENV_MAP_DIR" \
    --white_env_map_dir_path "$ENV_MAP_DIR" \
    --model_list_path "$MODEL_LIST_PATH" \
    --num_views "$NUM_VIEWS" \
    --num_test_views "$NUM_TEST_VIEWS" \
    --rendered_dir_name /music-shared-disk/group/ct/yiwen/data/objaverse/rendered_dense_polyhaven_test
}

if [[ "${1:-}" == "run_on_node" ]]; then
  echo "Running on compute node: PROJ=$PROJ GROUP_START=$GROUP_START GROUP_END=$GROUP_END OUTPUT_DIR=$OUTPUT_DIR"
  # Silence ALSA/audio warnings on headless node
  export SDL_AUDIODRIVER=dummy
  run_on_node
  exit 0
fi

# --- One-shot srun (reference: shortcuts.sh SRUN_OPTS + srun) ---
SRUN_OPTS="--partition=${PARTITION} --account=${ACCOUNT} --gres=gpu:1 --job-name=bpy_polyhaven"

echo "=============================================="
echo "Interactive: render_3dmodels_dense_polyhaven (srun one-shot)"
echo "=============================================="
echo "PROJ=$PROJ BLENDER_BIN=$BLENDER_BIN"
echo "GROUP_START=$GROUP_START GROUP_END=$GROUP_END OUTPUT_DIR=$OUTPUT_DIR"
echo "srun $SRUN_OPTS ..."
echo "=============================================="

cd "$PROJ"
srun $SRUN_OPTS bash -lc "
  set -e
  export SDL_AUDIODRIVER=dummy
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
