#!/bin/bash
# 批量提交所有渲染作业的脚本

echo "开始提交所有渲染作业..."

# 提交各个组的作业
echo "提交组 0-50..."
sbatch render_3dmodels_dense_0_50.sh

echo "提交组 50-100..."
sbatch render_3dmodels_dense_50_100.sh

echo "提交组 100-150..."
sbatch render_3dmodels_dense_100_150.sh

echo "提交组 150-200..."
sbatch render_3dmodels_dense_150_200.sh

echo "所有作业已提交完成!"
echo "使用 'squeue -u \$USER' 查看作业状态"
