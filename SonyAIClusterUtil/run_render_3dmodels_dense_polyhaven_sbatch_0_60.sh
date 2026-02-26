#!/bin/bash
#SBATCH --partition=ct
#SBATCH --account=ct
#SBATCH --requeue
#SBATCH --job-name=bpy_ph_0_60
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --output=slurm_logs/%x.%j.out
#SBATCH --error=slurm_logs/%x.%j.err
# =============================================================================
# sharedp: render_3dmodels_dense_polyhaven.py group 0-60 (60 items)
# Submit: cd /music-shared-disk/group/ct/yiwen/codes/render_objaverse && sbatch SonyAIClusterUtil/run_render_3dmodels_dense_polyhaven_sbatch_0_60.sh
# =============================================================================

set -euo pipefail

mkdir -p slurm_logs
export SDL_AUDIODRIVER=dummy

PROJ="${PROJ:-/music-shared-disk/group/ct/yiwen/codes/render_objaverse}"
BLENDER_BIN="${BLENDER_BIN:-${PROJ}/neuralGaufferRendering/blender-3.2.2-linux-x64/blender}"
[[ ! -x "$BLENDER_BIN" ]] && BLENDER_BIN="${PROJ}/neuralGaufferRendering/blender-4.2-linux-x64/blender"
if [[ ! -x "$BLENDER_BIN" ]]; then
  echo "Error: Blender not found."
  exit 1
fi

GROUP_START=0
GROUP_END=60
OUTPUT_DIR="/music-shared-disk/group/ct/yiwen/data/objaverse/rendered_dense_polyhaven"
MODEL_LQ_DIR="/music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_models"
ENV_MAP_DIR="/music-shared-disk/group/ct/yiwen/data/objaverse/hdris"
MODEL_LIST_PATH="${MODEL_LIST_PATH:-assets/object_ids/polyhaven_models_train.json}"
NUM_VIEWS=30
NUM_TEST_VIEWS=100
RENDERED_DIR_NAME="/music-shared-disk/group/ct/yiwen/data/objaverse/rendered_dense_polyhaven"

cd "$PROJ"
echo "Batch: render_3dmodels_dense_polyhaven group $GROUP_START-$GROUP_END (sharedp)"
"$BLENDER_BIN" -b -P render_3dmodels_dense_polyhaven.py -- \
  --group_start $GROUP_START \
  --group_end $GROUP_END \
  --output_dir "$OUTPUT_DIR" \
  --model_lq_dir "$MODEL_LQ_DIR" \
  --env_map_dir_path "$ENV_MAP_DIR" \
  --white_env_map_dir_path "$ENV_MAP_DIR" \
  --model_list_path "$MODEL_LIST_PATH" \
  --num_views $NUM_VIEWS \
  --num_test_views $NUM_TEST_VIEWS \
  --rendered_dir_name "$RENDERED_DIR_NAME" \
  --num_white_pls 3 --num_rgb_pls 1 --num_multi_pls 0 \
  --num_env_lights 0 --num_white_envs 1 --num_area_lights 0
echo "Done."
