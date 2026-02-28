#!/bin/bash
# Generate distributed 3D scene rendering scripts for Sony cluster
# Covers scenes 0-2302 (matching test_obj_curated.csv entries)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define scene ranges (50 scenes per batch)
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
  "1000 1050"
  "1050 1100"
  "1100 1150"
  "1150 1200"
  "1200 1250"
  "1250 1300"
  "1300 1350"
  "1350 1400"
  "1400 1450"
  "1450 1500"
  "1500 1550"
  "1550 1600"
  "1600 1650"
  "1650 1700"
  "1700 1750"
  "1750 1800"
  "1800 1850"
  "1850 1900"
  "1900 1950"
  "1950 2000"
  "2000 2050"
  "2050 2100"
  "2100 2150"
  "2150 2200"
  "2200 2250"
  "2250 2302"
)

echo "Generating ${#RANGES[@]} scene rendering scripts..."

for range in "${RANGES[@]}"; do
  read -r START END <<< "$range"
  
  SCRIPT_FILE="${SCRIPT_DIR}/run_render_3dscenes_distributed_${START}_${END}.sh"
  
  cat > "$SCRIPT_FILE" <<EOF
#!/bin/bash
#SBATCH --partition=sharedp
#SBATCH --account=ct
#SBATCH --requeue
#SBATCH --job-name=render_scenes_${START}_${END}
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --output=slurm_logs/%x.%j.out
#SBATCH --error=slurm_logs/%x.%j.err
# =============================================================================
# Multi-worker distributed rendering: 3D scenes ${START}-${END} with 4 workers per GPU
# Submit: cd /music-shared-disk/group/ct/yiwen/codes/render_objaverse && \\
#   sbatch SonyAIClusterUtil/run_render_3dscenes_distributed_${START}_${END}.sh
# =============================================================================

set -euo pipefail

mkdir -p slurm_logs
export SDL_AUDIODRIVER=dummy

PROJ="/music-shared-disk/group/ct/yiwen/codes/render_objaverse"
cd "\$PROJ"

# Multi-worker: 4 Blender processes per GPU
python3 SonyAIClusterUtil/distribute_render_3dscenes_sony.py \\
  --num_gpus 1 \\
  --workers_per_gpu 4 \\
  --group_start ${START} \\
  --group_end ${END} \\
  --num_views 30 \\
  --num_test_views 50 \\
  --num_white_envs 1 \\
  --num_env_lights 3 \\
  --num_white_pls 3 \\
  --num_rgb_pls 1 \\
  --num_multi_pls 0 \\
  --num_area_lights 0 \\
  --num_combined_lights 0 \\
  --model_lq_dir /music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_models \\
  --output_dir /music-shared-disk/group/ct/yiwen/data/objaverse/rendered_scenes_dense \\
  --texture_dir /music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_textures \\
  --env_map_dir /music-shared-disk/group/ct/yiwen/data/objaverse/hdris \\
  --glb_list_path test_obj_curated.csv \\
  --glbs_root_path /music-shared-disk/group/ct/yiwen/data/objaverse/objaverse/hf-objaverse-v1/glbs/ \\
  --proj_root "\$PROJ"

echo "Done."
EOF

  chmod +x "$SCRIPT_FILE"
  echo "Created: $(basename $SCRIPT_FILE) (scenes ${START}-${END})"
done

echo ""
echo "✅ Generated ${#RANGES[@]} scripts!"
echo ""
echo "Submit all jobs:"
echo "  cd /music-shared-disk/group/ct/yiwen/codes/render_objaverse"
echo "  bash SonyAIClusterUtil/submit_all_render_3dscenes.sh"
