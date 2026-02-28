#!/bin/bash
#SBATCH --partition=sharedp
#SBATCH --account=ct
#SBATCH --requeue
#SBATCH --job-name=download_objaverse
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --time=48:00:00
#SBATCH --mem=32
#SBATCH --output=slurm_logs/download_objaverse.%j.out
#SBATCH --error=slurm_logs/download_objaverse.%j.err
# =============================================================================
# Download objaverse objects using system Python + venv
# Submit: cd /music-shared-disk/group/ct/yiwen/codes/render_objaverse && \
#   sbatch SonyAIClusterUtil/download_objaverse_venv.sh
# =============================================================================

set -euo pipefail
mkdir -p slurm_logs

PROJ="/music-shared-disk/group/ct/yiwen/codes/render_objaverse"
cd "$PROJ"

# Virtual environment for objaverse
VENV_DIR="${VENV_DIR:-/scratch2/$USER/venv/objaverse_download}"

# Download parameters
OBJ_LIST="test_obj_curated.csv"
END_UID=15000
BASE_PATH="/music-shared-disk/group/ct/yiwen/data/objaverse"

echo "========================================"
echo "Setting up objaverse environment"
echo "========================================"

# Create venv if it doesn't exist
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Install objaverse
echo "Installing/upgrading objaverse..."
pip install --upgrade pip
pip install objaverse

echo ""
echo "========================================"
echo "Downloading objaverse objects"
echo "Object list: $OBJ_LIST"
echo "End UID: $END_UID"
echo "Base path: $BASE_PATH"
echo "========================================"

# Run download script
python download.py \
  --obj_list "$OBJ_LIST" \
  --end_uid $END_UID \
  --base_path "$BASE_PATH"

echo "Done."
