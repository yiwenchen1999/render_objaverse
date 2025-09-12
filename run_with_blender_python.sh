#!/bin/bash

# 使用 Blender 的 Python 运行渲染脚本
# 这个脚本会使用 Blender 自带的 Python 环境，其中已经包含了 bpy 模块

# Blender Python 路径
BLENDER_PYTHON="/Applications/Blender.app/Contents/Resources/4.5/python/bin/python3.11"

# 检查 Blender Python 是否存在
if [ ! -f "$BLENDER_PYTHON" ]; then
    echo "错误: 找不到 Blender Python 在 $BLENDER_PYTHON"
    echo "请确保 Blender 已正确安装"
    exit 1
fi

# 设置 Python 路径，包含当前目录和 bpy_helper 模块
export PYTHONPATH="${PYTHONPATH}:$(pwd):$(pwd)/bpy_helper"

# 安装必要的 Python 包到 Blender 的 Python 环境
echo "安装必要的 Python 包..."
$BLENDER_PYTHON -m pip install --upgrade pip
$BLENDER_PYTHON -m pip install numpy imageio simple-parsing

# 运行渲染脚本
echo "使用 Blender Python 运行渲染脚本..."
$BLENDER_PYTHON render_3dmodels_dense.py "$@"
