#!/bin/bash
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --time=8:00:00
#SBATCH --job-name=download_render_lvis_6000_9000
#SBATCH --mem=32
#SBATCH --ntasks=4
#SBATCH --gres=gpu:1
#SBATCH --output=myjob.download_render_lvis_6000_9000.out
#SBATCH --error=myjob.download_render_lvis_6000_9000.err

# # 设置工作目录（根据实际路径调整）
# SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
# cd "$PROJECT_DIR"

# echo "工作目录: $(pwd)"
# echo ""

# # 步骤 1: 下载模型 (索引 0-9000)
# echo "=========================================="
# echo "步骤 1: 开始下载模型 (索引 0-9000)"
# echo "=========================================="
# echo "时间: $(date)"
# python download_lvis.py \
#     --csv_path ./filtered_uids_lvis.csv \
#     --base_path /projects/vig/Datasets \
#     --begin_uid 0 \
#     --end_uid 9000

# DOWNLOAD_EXIT_CODE=$?
# if [ $DOWNLOAD_EXIT_CODE -ne 0 ]; then
#     echo "错误: 下载模型失败 (退出码: $DOWNLOAD_EXIT_CODE)，停止执行"
#     exit 1
# fi

# echo "下载完成！时间: $(date)"
# echo ""

# 步骤 2: 渲染预览图 (索引 6000-9000)
echo "=========================================="
echo "步骤 2: 开始渲染预览图 (索引 6000-9000)"
echo "=========================================="
echo "时间: $(date)"
python render_previews_lvis.py \
    --csv_path ./filtered_uids_lvis.csv \
    --group_start 6000 \
    --group_end 9000

RENDER_EXIT_CODE=$?
if [ $RENDER_EXIT_CODE -ne 0 ]; then
    echo "错误: 渲染预览图失败 (退出码: $RENDER_EXIT_CODE)"
    exit 1
fi

echo "=========================================="
echo "所有任务完成！"
echo "完成时间: $(date)"
echo "=========================================="

