#!/bin/bash
# 本地运行下载脚本

echo "开始下载test_obj.csv中的所有对象..."
echo "开始时间: $(date)"

# 检查必要文件
if [ ! -f "test_obj.csv" ]; then
    echo "错误: 找不到 test_obj.csv 文件"
    exit 1
fi

if [ ! -f "download.py" ]; then
    echo "错误: 找不到 download.py 文件"
    exit 1
fi

# 运行下载脚本
python3 download_test_objects.py

echo "结束时间: $(date)"
echo "下载任务完成!"
