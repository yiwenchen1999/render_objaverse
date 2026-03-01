#!/bin/bash
# 批量提交所有渲染作业的脚本

echo "开始提交所有渲染作业..."

# 提交各个组的作业
echo "提交组 0_50..."
sbatch scripts/render_3dmodels_dense_500_550.sh

echo "提交组 50_100..."
sbatch scripts/render_3dmodels_dense_550_600.sh

echo "提交组 100_150..."
sbatch scripts/render_3dmodels_dense_600_650.sh

echo "提交组 150_200..."
sbatch scripts/render_3dmodels_dense_650_700.sh

echo "提交组 200_250..."
sbatch scripts/render_3dmodels_dense_700_750.sh

echo "提交组 250_300..."
sbatch scripts/render_3dmodels_dense_750_800.sh

echo "提交组 300_350..."
sbatch scripts/render_3dmodels_dense_800_850.sh

echo "提交组 350_400..."
sbatch scripts/render_3dmodels_dense_850_900.sh

echo "所有作业已提交完成!"
echo "使用 'squeue -u \$USER' 查看作业状态"
