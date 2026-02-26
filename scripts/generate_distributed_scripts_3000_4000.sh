#!/bin/bash
# =============================================================================
# Generate distributed sbatch scripts for scene ranges 3000-4000 (8 scripts)
# Usage: bash scripts/generate_distributed_scripts_3000_4000.sh
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Define ranges: 3000-4000, 8 scripts, 125 scenes each
RANGES=(
  "3000 3125"
  "3125 3250"
  "3250 3375"
  "3375 3500"
  "3500 3625"
  "3625 3750"
  "3750 3875"
  "3875 4000"
)

for range in "${RANGES[@]}"; do
  read -r START END <<< "$range"
  
  SCRIPT_NAME="distribute_render_3dscenes_${START}_${END}.sh"
  
  cat > "$SCRIPT_NAME" <<EOF
#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=60:00:00
#SBATCH --job-name=render_scenes_dist_${START}_${END}
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:a5000:1
#SBATCH --output=myjob.render_scenes_dist_${START}_${END}.out
#SBATCH --error=myjob.render_scenes_dist_${START}_${END}.err
# =============================================================================
# Multi-worker distributed rendering: scenes ${START}-${END} with 4 workers per GPU
# Submit: cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse && \\
#   sbatch scripts/distribute_render_3dscenes_${START}_${END}.sh
# Prerequisite: conda activate blender-env (before submitting)
# =============================================================================

cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

python scripts/distribute_render_3dscenes.py \\
  --num_gpus 1 \\
  --workers_per_gpu 4 \\
  --group_start ${START} \\
  --group_end ${END} \\
  --num_white_envs 1 \\
  --num_env_lights 3 \\
  --model_lq_dir /projects/vig/Datasets/Polyhaven/polyhaven_models \\
  --output_dir ./output_scenes_dense \\
  --texture_dir /projects/vig/Datasets/Polyhaven/polyhaven_textures \\
  --glb_list_path test_obj_curated.csv \\
  --glbs_root_path /projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/ \\
  --proj_root /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

echo "Done."
EOF
  
  chmod +x "$SCRIPT_NAME"
  echo "Created: $SCRIPT_NAME"
done

echo ""
echo "All distributed scripts (3000-4000) generated!"
echo "To submit all jobs:"
echo "  for script in scripts/distribute_render_3dscenes_3*_*.sh; do sbatch \$script; done"
