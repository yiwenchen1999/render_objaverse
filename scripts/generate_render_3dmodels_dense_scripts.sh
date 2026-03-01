#!/bin/bash
# Generate multiple SBATCH scripts for distributed 3D model rendering (dense)
# Usage: bash scripts/generate_render_3dmodels_dense_scripts.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ_ROOT="/projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse"

# Define model ranges (50 models per batch)
RANGES=(
  "7000 7050"
  "7050 7100"
  "7100 7150"
  "7150 7200"
  "7200 7250"
  "7250 7300"
  "7300 7350"
  "7350 7400"
  "7400 7450"
  "7450 7500"
  "7500 7550"
  "7550 7600"
  "7600 7650"
  "7650 7700"
  "7700 7750"
  "7750 7800"
  "7800 7850"
  "7850 7900"
  "7900 7950"
  "7950 8000"
  "8000 8050"
  "8050 8100"
  "8100 8150"
  "8150 8200"
  "8200 8250"
  "8250 8300"
  "8300 8350"
  "8350 8400"
  "8400 8450"
  "8450 8500"
  "8500 8550"
  "8550 8600"
  "8600 8650"
  "8650 8700"
  "8700 8750"
  "8750 8800"
  "8800 8850"
  "8850 8900"
  "8900 8950"
  "8950 9000"
)

echo "Generating ${#RANGES[@]} model rendering scripts..."

for range in "${RANGES[@]}"; do
  read -r START END <<< "$range"
  
  SCRIPT_FILE="${SCRIPT_DIR}/render_3dmodels_dense_${START}_${END}.sh"
  
  # Determine partition and GPU based on range
  # Default: jiang partition, a5000 GPU
  PARTITION="jiang"
  GPU_TYPE="a5000:1"
  TIME="60:00:00"
  
  # Special case (500-900): gpu partition, generic gpu (from 650-700 template)
  if [ "$START" -ge 500 ] && [ "$END" -le 900 ]; then
    PARTITION="gpu"
    GPU_TYPE="1"
    TIME="8:00:00"
  fi
  
  cat > "$SCRIPT_FILE" <<EOF
#!/bin/bash
#SBATCH --partition=${PARTITION}
#SBATCH --nodes=1
#SBATCH --time=${TIME}
#SBATCH --job-name=render_models_dense_dist_${START}_${END}
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --gres=gpu:${GPU_TYPE}
#SBATCH --output=myjob.render_models_dense_dist_${START}_${END}.out
#SBATCH --error=myjob.render_models_dense_dist_${START}_${END}.err
# =============================================================================
# Multi-worker distributed rendering: models ${START}-${END} with 2 workers per GPU
# Submit: cd ${PROJ_ROOT} && \\
#   sbatch scripts/render_3dmodels_dense_${START}_${END}.sh
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
  --num_white_pls 1 \\
  --num_rgb_pls 1 \\
  --num_multi_pls 1 \\
  --num_area_lights 1 \\
  --num_combined_lights 4 \\
  --rendered_dir_name rendered_dense_lightPlus \\
  --csv_path test_obj.csv \\
  --proj_root ${PROJ_ROOT}

echo "Done."
EOF

  chmod +x "$SCRIPT_FILE"
  echo "Created: $(basename $SCRIPT_FILE) (models ${START}-${END}) [Partition: ${PARTITION}]"
done

echo ""
echo "✅ Generated ${#RANGES[@]} scripts!"
