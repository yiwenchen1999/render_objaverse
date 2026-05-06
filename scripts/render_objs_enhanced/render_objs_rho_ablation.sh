#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=60:00:00
#SBATCH --job-name=render_objs_rho_ablation
#SBATCH --mem=32
#SBATCH --ntasks=4
#SBATCH --gres=gpu:a5000:1
#SBATCH --output=myjob.render_objs_rho_ablation.out
#SBATCH --error=myjob.render_objs_rho_ablation.err

set -euo pipefail

cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

# Render exactly one model per rho range for ablation.
MODEL_IDX=18200
PROJ_ROOT=/projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

RHO_MINS=(0.5 0.6 0.7 0.8 0.9 1.0 1.1 1.2)
RHO_MAXS=(0.6 0.7 0.8 0.9 1.0 1.1 1.2 1.3)

for i in "${!RHO_MINS[@]}"; do
  RMIN="${RHO_MINS[$i]}"
  RMAX="${RHO_MAXS[$i]}"
  OUT_DIR="rendered_objs_rho${RMIN}-${RMAX}"

  echo "Rendering model ${MODEL_IDX} with rho range [${RMIN}, ${RMAX}] -> ${OUT_DIR}"
  python scripts/distribute_render_3dmodels_dense_enhance.py \
    --num_gpus 1 \
    --workers_per_gpu 1 \
    --group_start "${MODEL_IDX}" \
    --group_end "$((MODEL_IDX + 1))" \
    --num_views 1 \
    --num_test_views 1 \
    --dynamic_lighting_counts \
    --enable_combined \
    --combined_probability 0.25 \
    --lighting_seed 2022 \
    --rho_min "${RMIN}" \
    --rho_max "${RMAX}" \
    --rendered_dir_name "${OUT_DIR}" \
    --csv_path test_obj.csv \
    --proj_root "${PROJ_ROOT}"
done

echo "Rho ablation rendering done."
