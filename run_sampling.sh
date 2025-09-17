#!/bin/bash

# 脚本用于运行对象采样程序
# 从JSON和CSV文件中分别采样20个对象并复制到指定目录

echo "开始运行对象采样脚本..."
echo "当前工作目录: $(pwd)"

# 检查Python脚本是否存在
if [ ! -f "sample_objects.py" ]; then
    echo "错误: 找不到 sample_objects.py 文件"
    exit 1
fi

# 检查源数据文件是否存在
if [ ! -f "all_objaverse_filtered_data.json" ]; then
    echo "错误: 找不到 all_objaverse_filtered_data.json 文件"
    exit 1
fi

if [ ! -f "filtered_uids.csv" ]; then
    echo "错误: 找不到 filtered_uids.csv 文件"
    exit 1
fi

# 检查源数据目录是否存在
SOURCE_DIR="/projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/"
if [ ! -d "$SOURCE_DIR" ]; then
    echo "警告: 源数据目录不存在: $SOURCE_DIR"
    echo "请确保路径正确，或者修改脚本中的路径"
fi

# 运行Python脚本
echo "运行采样脚本..."
python3 sample_objects.py

echo "采样脚本执行完成!"
