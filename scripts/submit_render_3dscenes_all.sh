#!/bin/bash
# Submit all render_3dscenes jobs

echo "Submitting all render_3dscenes jobs..."

sbatch scripts/render_3dscenes_0_50.sh
sbatch scripts/render_3dscenes_50_100.sh
sbatch scripts/render_3dscenes_100_150.sh
sbatch scripts/render_3dscenes_150_200.sh
sbatch scripts/render_3dscenes_200_250.sh
sbatch scripts/render_3dscenes_250_300.sh
sbatch scripts/render_3dscenes_300_350.sh
sbatch scripts/render_3dscenes_350_400.sh
sbatch scripts/render_3dscenes_400_450.sh
sbatch scripts/render_3dscenes_450_500.sh
sbatch scripts/render_3dscenes_500_550.sh
sbatch scripts/render_3dscenes_550_600.sh
sbatch scripts/render_3dscenes_600_650.sh
sbatch scripts/render_3dscenes_650_700.sh
sbatch scripts/render_3dscenes_700_750.sh
sbatch scripts/render_3dscenes_750_800.sh
sbatch scripts/render_3dscenes_800_850.sh
sbatch scripts/render_3dscenes_850_900.sh
sbatch scripts/render_3dscenes_900_950.sh
sbatch scripts/render_3dscenes_950_1000.sh

echo "All jobs submitted!"
echo "Use 'squeue -u \$USER' to check job status"