#!/bin/bash
# Render SF3D meshes per scene under a data_root, using the per-scene context
# envmap to light each mesh. Run from the repo root or pass DATA_ROOT.
#
# Usage:
#   bash scripts/render_sf3d_mesh/render_sf3d_mesh.sh [DATA_ROOT] [ITER_SUBDIR]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

DATA_ROOT="${1:-/projects/vig/Datasets/objaverse/hf-objaverse-v1/demo_scene/}"
ITER_SUBDIR="${2:-iter_00000297}"
RESOLUTION="${RESOLUTION:-512}"
FOV_DEG="${FOV_DEG:-30}"
CYCLES_SAMPLES="${CYCLES_SAMPLES:-128}"
ENV_ROTATION_Z="${ENV_ROTATION_Z:-0.0}"
ENV_STRENGTH="${ENV_STRENGTH:-1.0}"
TARGET_SCALE="${TARGET_SCALE:-0.22}"
NUM_TARGET_VIEWS="${NUM_TARGET_VIEWS:-8}"
# 1 → pass --normalize (bounding sphere)
NORMALIZE="${NORMALIZE:-1}"
# 1 → pass --skip_target_views (context view only)
SKIP_TARGET_VIEWS="${SKIP_TARGET_VIEWS:-0}"
# 1 → keep env rotation as identity (no world-rotation R applied to env)
NO_ALIGN_ENV="${NO_ALIGN_ENV:-0}"
PYTHON_BIN="${PYTHON_BIN:-python}"

EXTRA_ARGS=()
if [ -n "${SCENE_FILTER:-}" ]; then
  EXTRA_ARGS+=(--scene_filter "${SCENE_FILTER}")
fi
if [ "${NORMALIZE}" = "1" ]; then
  EXTRA_ARGS+=(--normalize)
fi
if [ "${SKIP_TARGET_VIEWS}" = "1" ]; then
  EXTRA_ARGS+=(--skip_target_views)
fi
if [ "${NO_ALIGN_ENV}" = "1" ]; then
  EXTRA_ARGS+=(--align_env=False)
fi

echo "[render_sf3d_mesh] data_root=${DATA_ROOT} iter_subdir=${ITER_SUBDIR}"

"${PYTHON_BIN}" render_sf3d_meshes.py \
  --data_root "${DATA_ROOT}" \
  --iter_subdir "${ITER_SUBDIR}" \
  --resolution "${RESOLUTION}" \
  --fov_deg "${FOV_DEG}" \
  --cycles_samples "${CYCLES_SAMPLES}" \
  --env_rotation_z "${ENV_ROTATION_Z}" \
  --env_strength "${ENV_STRENGTH}" \
  --target_scale "${TARGET_SCALE}" \
  --num_target_views "${NUM_TARGET_VIEWS}" \
  "${EXTRA_ARGS[@]}"
