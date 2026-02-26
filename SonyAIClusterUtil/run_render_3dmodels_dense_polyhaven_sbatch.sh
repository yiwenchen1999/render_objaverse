#!/bin/bash
#SBATCH --partition=ct
#SBATCH --account=ct
#SBATCH --job-name=bpy_polyhaven
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --output=slurm_logs/%x.%j.out
#SBATCH --error=slurm_logs/%x.%j.err
# =============================================================================
# Sony cluster: batch run for render_3dmodels_dense_polyhaven.py
# Reference: shortcuts.sh, sonyai_crusoe_day1_quickstart.md (sbatch format)
#
# Submit: cd /music-shared-disk/group/ct/yiwen/codes/render_objaverse && sbatch SonyAIClusterUtil/run_render_3dmodels_dense_polyhaven_sbatch.sh
#
# Override before sbatch: export GROUP_START=0 GROUP_END=50 OUTPUT_DIR=/scratch2/$USER/out
# For sharedp (preemptible): add --partition=ct,sharedp and #SBATCH --requeue
# Prereq: Run once: bash SonyAIClusterUtil/install_blender_python_deps.sh
# =============================================================================

set -euo pipefail

mkdir -p slurm_logs
export SDL_AUDIODRIVER=dummy

PROJ="${PROJ:-/music-shared-disk/group/ct/yiwen/codes/render_objaverse}"
BLENDER_BIN="${BLENDER_BIN:-${PROJ}/blender-4.2-linux-x64/blender}"
if [[ ! -x "$BLENDER_BIN" ]]; then
  BLENDER_BIN="${PROJ}/neuralGaufferRendering/blender-3.2.2-linux-x64/blender"
fi
if [[ ! -x "$BLENDER_BIN" ]]; then
  echo "Error: Blender not found. Set BLENDER_BIN or install Blender in project."
  exit 1
fi

GROUP_START="${GROUP_START:-0}"
GROUP_END="${GROUP_END:-10}"
OUTPUT_DIR="${OUTPUT_DIR:-/scratch2/$USER/rendered_dense_polyhaven}"
MODEL_LQ_DIR="${MODEL_LQ_DIR:-/music-shared-disk/group/ct/yiwen/data/Polyhaven/polyhaven_models}"
ENV_MAP_DIR="${ENV_MAP_DIR:-/music-shared-disk/group/ct/yiwen/data/envmaps/hdris}"
MODEL_LIST_PATH="${MODEL_LIST_PATH:-assets/object_ids/polyhaven_models_train.json}"
NUM_VIEWS="${NUM_VIEWS:-200}"
NUM_TEST_VIEWS="${NUM_TEST_VIEWS:-100}"

cd "$PROJ"

echo "=============================================="
echo "Batch: render_3dmodels_dense_polyhaven"
echo "=============================================="
echo "PROJ=$PROJ BLENDER_BIN=$BLENDER_BIN"
echo "GROUP_START=$GROUP_START GROUP_END=$GROUP_END OUTPUT_DIR=$OUTPUT_DIR"
echo "=============================================="

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
  --rendered_dir_name rendered_dense_polyhaven

echo "Done."
