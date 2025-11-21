#!/bin/bash
# 批量提交所有渲染作业的脚本

echo "开始提交所有渲染作业..."

# 提交各个组的作业

echo "提交组 400-450..."
sbatch render_3dmodels_dense_400_450.sh

echo "提交组 450-500..."
sbatch render_3dmodels_dense_450_500.sh

echo "所有作业已提交完成!"
echo "使用 'squeue -u \$USER' 查看作业状态"
