#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=24:00:00
#SBATCH --job-name=render_sf3d_mesh
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:a5000:1
#SBATCH --output=myjob.render_sf3d_mesh.out
#SBATCH --error=myjob.render_sf3d_mesh.err

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

# Override these via environment variables if needed.
PYTHON_BIN="${PYTHON_BIN:-python}"
SCENE_REPO_DIR="${SCENE_REPO_DIR:-/projects/vig/Datasets/objaverse/hf-objaverse-v1/sf3d_meshes}"
OUTPUT_SUBDIR="${OUTPUT_SUBDIR:-rerendered}"
RESOLUTION="${RESOLUTION:-256}"
FOV_DEG="${FOV_DEG:-30}"
DEVICE="${DEVICE:-GPU}"
SAMPLES="${SAMPLES:-64}"
MAX_SCENES="${MAX_SCENES:--1}"
TARGET_ENV_INDEX="${TARGET_ENV_INDEX:-1}"
ENV_STRENGTH="${ENV_STRENGTH:-1.0}"
VERBOSE="${VERBOSE:-1}"

CMD=(
  "${PYTHON_BIN}" "render_sf3d_rerender.py"
  --repo-dir "${SCENE_REPO_DIR}"
  --output-subdir "${OUTPUT_SUBDIR}"
  --resolution "${RESOLUTION}"
  --fov-deg "${FOV_DEG}"
  --device "${DEVICE}"
  --samples "${SAMPLES}"
  --max-scenes "${MAX_SCENES}"
  --target-env-index "${TARGET_ENV_INDEX}"
  --env-strength "${ENV_STRENGTH}"
)

if [[ "${VERBOSE}" == "1" ]]; then
  CMD+=(--verbose)
fi

echo "Running command:"
printf ' %q' "${CMD[@]}"
echo

"${CMD[@]}"
