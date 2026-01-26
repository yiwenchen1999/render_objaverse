#!/bin/bash
# 批量提交所有渲染作业的脚本

echo "开始提交所有渲染作业..."

# 提交各个组的作业
echo "提交组 200-250..."
sbatch scripts/render_3dmodels_dense_700-750.sh

echo "提交组 250-300..."
sbatch scripts/render_3dmodels_dense_750-800.sh

echo "提交组 300-350..."
sbatch scripts/render_3dmodels_dense_800-850.sh

echo "提交组 350-400..."
sbatch scripts/render_3dmodels_dense_850-900.sh

echo "提交组 900-950..."
sbatch scripts/render_3dmodels_dense_900-950.sh

echo "提交组 950-1000..."
sbatch scripts/render_3dmodels_dense_950-1000.sh
    
echo "所有作业已提交完成!"
echo "使用 'squeue -u \$USER' 查看作业状态"
