#!/bin/bash
# =============================================================================
# Generate distributed sbatch scripts for all scene ranges (0-50, 50-100, ...)
# Usage: bash scripts/generate_all_distributed_scripts.sh
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Define ranges (matching existing scripts)
RANGES=(
  "0 50"
  "50 100"
  "100 150"
  "150 200"
  "200 250"
  "250 300"
  "300 350"
  "350 400"
  "400 450"
  "450 500"
  "500 550"
  "550 600"
  "600 650"
  "650 700"
  "700 750"
  "750 800"
  "800 850"
  "850 900"
  "900 950"
  "950 1000"
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
  --num_white_pls 0 \\
  --num_rgb_pls 0 \\
  --num_multi_pls 0 \\
  --num_area_lights 0 \\
  --model_lq_dir /projects/vig/Datasets/Polyhaven/polyhaven_models \\
  --output_dir ./output_scenes_dense \\
  --texture_dir /projects/vig/Datasets/Polyhaven/polyhaven_textures \\
  --glb_list_path test_obj_curated.csv \\
  --glbs_root_path /projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/ \\
  --num_white_pls 0 \\
  --num_rgb_pls 0 \\
  --num_multi_pls 0 \\
  --num_area_lights 0 \\
  --proj_root /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

echo "Done."
EOF
  
  chmod +x "$SCRIPT_NAME"
  echo "Created: $SCRIPT_NAME"
done

echo ""
echo "All distributed scripts generated!"
echo "To submit all jobs:"
echo "  for i in {0..19}; do sbatch scripts/distribute_render_3dscenes_*_*.sh; done"
