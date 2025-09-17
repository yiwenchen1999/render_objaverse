#!/bin/bash
# 批量提交所有渲染作业的脚本

echo "开始提交所有渲染作业..."

# 提交各个组的作业
echo "提交组 200-250..."
sbatch render_3dmodels_dense_200_250.sh

echo "提交组 250-300..."
sbatch render_3dmodels_dense_250_300.sh

echo "提交组 300-350..."
sbatch render_3dmodels_dense_300_350.sh

echo "提交组 350-400..."
sbatch render_3dmodels_dense_350_400.sh

echo "提交组 400-450..."
sbatch render_3dmodels_dense_400_450.sh

echo "提交组 450-500..."
sbatch render_3dmodels_dense_450_500.sh

echo "所有作业已提交完成!"
echo "使用 'squeue -u \$USER' 查看作业状态"
