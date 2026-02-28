#!/bin/bash
# Generate multiple SBATCH scripts for distributed 3D model rendering with addLights
# Usage: bash scripts/generate_render_3dmodels_addLights_scripts.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ_ROOT="/projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse"

# Define model ranges (50 models per batch)
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
)

echo "Generating ${#RANGES[@]} model rendering scripts..."

for range in "${RANGES[@]}"; do
  read -r START END <<< "$range"
  
  SCRIPT_FILE="${SCRIPT_DIR}/render_3dmodels_addLights_${START}_${END}.sh"
  
  cat > "$SCRIPT_FILE" <<EOF
#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=60:00:00
#SBATCH --job-name=render_models_addLights_dist_${START}_${END}
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:a5000:1
#SBATCH --output=myjob.render_models_addLights_dist_${START}_${END}.out
#SBATCH --error=myjob.render_models_addLights_dist_${START}_${END}.err
# =============================================================================
# Multi-worker distributed rendering: models ${START}-${END} with 2 workers per GPU
# Submit: cd ${PROJ_ROOT} && \\
#   sbatch scripts/render_3dmodels_addLights_${START}_${END}.sh
# =============================================================================

cd ${PROJ_ROOT}

python scripts/distribute_render_3dmodels_addLights.py \\
  --num_gpus 1 \\
  --workers_per_gpu 2 \\
  --group_start ${START} \\
  --group_end ${END} \\
  --num_views 30 \\
  --num_test_views 50 \\
  --num_white_envs 1 \\
  --num_env_lights 0 \\
  --num_white_pls 3 \\
  --num_rgb_pls 1 \\
  --num_multi_pls 0 \\
  --num_area_lights 0 \\
  --num_combined_lights 0 \\
  --rendered_dir_name rendered_dense_lightPlus \\
  --csv_path test_obj.csv \\
  --proj_root ${PROJ_ROOT}

echo "Done."
EOF

  chmod +x "$SCRIPT_FILE"
  echo "Created: $(basename $SCRIPT_FILE) (models ${START}-${END})"
done

echo ""
echo "✅ Generated ${#RANGES[@]} scripts!"
echo ""
echo "Submit individual jobs:"
echo "  cd ${PROJ_ROOT}"
echo "  sbatch scripts/render_3dmodels_addLights_0_50.sh"
echo ""
echo "Or create a master submit script to submit all at once."
