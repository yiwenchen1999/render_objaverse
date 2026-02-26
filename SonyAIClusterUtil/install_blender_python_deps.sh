#!/bin/bash
# =============================================================================
# Install Python deps (imageio, simple_parsing) into Blender's bundled Python
# so that render_3dmodels_dense_polyhaven.py can run inside Blender.
#
# Run once on the cluster (e.g. after sbash or on login node):
#   cd /music-shared-disk/group/ct/yiwen/codes/render_objaverse
#   bash SonyAIClusterUtil/install_blender_python_deps.sh
#
# Uses Blender 3.2.2 path; override with BLENDER_BIN or BLENDER_PYTHON.
# =============================================================================

set -euo pipefail

PROJ="${PROJ:-/music-shared-disk/group/ct/yiwen/codes/render_objaverse}"
BLENDER_BIN="${BLENDER_BIN:-${PROJ}/neuralGaufferRendering/blender-3.2.2-linux-x64/blender}"

# Blender 3.2.2: Python is at <blender-dir>/3.2/python/bin/python3
BLENDER_DIR="$(dirname "$BLENDER_BIN")"
if [[ -x "${BLENDER_DIR}/3.2/python/bin/python3" ]]; then
  BLENDER_PYTHON="${BLENDER_DIR}/3.2/python/bin/python3"
  PYVER="$("$BLENDER_PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")"
  SITE_PACKAGES="${BLENDER_DIR}/3.2/python/lib/python${PYVER}/site-packages"
  mkdir -p "$SITE_PACKAGES"
elif [[ -n "${BLENDER_PYTHON:-}" && -x "$BLENDER_PYTHON" ]]; then
  SITE_PACKAGES="$("$BLENDER_PYTHON" -c "import site; print(site.getsitepackages()[0])" 2>/dev/null)" || true
  mkdir -p "$SITE_PACKAGES"
else
  echo "Error: Could not find Blender's Python. Set BLENDER_PYTHON or use Blender 3.2.2 in neuralGaufferRendering."
  exit 1
fi

echo "Blender Python: $BLENDER_PYTHON"
echo "Target site-packages: $SITE_PACKAGES"

"$BLENDER_PYTHON" -m pip install --upgrade pip -q
"$BLENDER_PYTHON" -m pip install imageio simple_parsing --target "$SITE_PACKAGES"

echo "Done. Verify with: $BLENDER_PYTHON -c 'import imageio, simple_parsing; print(\"OK\")'"
"$BLENDER_PYTHON" -c 'import imageio, simple_parsing; print("OK")'
