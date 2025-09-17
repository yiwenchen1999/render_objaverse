#!/bin/bash
#SBATCH --partition=jiang
#SBATCH --nodes=1
#SBATCH --time=24:00:00
#SBATCH --job-name=download_test_objects
#SBATCH --mem=16
#SBATCH --ntasks=4
#SBATCH --output=myjob.download_test_objects.out
#SBATCH --error=myjob.download_test_objects.err

echo "开始下载test_obj.csv中的所有对象..."
echo "作业开始时间: $(date)"

# 运行下载脚本
python3 download_test_objects.py

echo "作业结束时间: $(date)"
echo "下载任务完成!"
