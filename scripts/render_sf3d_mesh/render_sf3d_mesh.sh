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

DATA_ROOT="${1:-/projects/vig/Datasets/objaverse/hf-objaverse-v1/sf3d_meshes}"
ITER_SUBDIR="${2:-iter_00000297}"
RESOLUTION="${RESOLUTION:-512}"
FOV_DEG="${FOV_DEG:-30}"
CYCLES_SAMPLES="${CYCLES_SAMPLES:-128}"
ENV_ROTATION_Z="${ENV_ROTATION_Z:-0.0}"
ENV_STRENGTH="${ENV_STRENGTH:-1.0}"
PYTHON_BIN="${PYTHON_BIN:-python}"

EXTRA_ARGS=()
if [ -n "${SCENE_FILTER:-}" ]; then
  EXTRA_ARGS+=(--scene_filter "${SCENE_FILTER}")
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
  "${EXTRA_ARGS[@]}"
