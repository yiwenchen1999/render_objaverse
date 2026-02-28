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
# Download objaverse objects using singularity container
# Submit: cd /music-shared-disk/group/ct/yiwen/codes/render_objaverse && \
#   sbatch SonyAIClusterUtil/download_objaverse_singularity.sh
# =============================================================================

set -euo pipefail
mkdir -p slurm_logs

PROJ="/music-shared-disk/group/ct/yiwen/codes/render_objaverse"
cd "$PROJ"

# Singularity image path (same as other Sony cluster scripts)
SIF="${SIF:-/scratch2/$USER/singularity_images/pytorch_24.01-py3.sif}"

# Bind mounts for data access
BIND="--bind /music-shared-disk:/music-shared-disk,/scratch2:/scratch2"

# Download parameters
OBJ_LIST="test_obj_curated.csv"
END_UID=15000
BASE_PATH="/music-shared-disk/group/ct/yiwen/data/objaverse"

echo "========================================"
echo "Downloading objaverse objects"
echo "Object list: $OBJ_LIST"
echo "End UID: $END_UID"
echo "Base path: $BASE_PATH"
echo "Singularity image: $SIF"
echo "========================================"

# Run in singularity with objaverse installed
singularity exec --nv $BIND $SIF bash -lc "
  # Install objaverse if not already installed
  pip install --user objaverse || true
  
  # Run download script
  cd $PROJ
  python download.py \
    --obj_list $OBJ_LIST \
    --end_uid $END_UID \
    --base_path $BASE_PATH
"

echo "Done."
