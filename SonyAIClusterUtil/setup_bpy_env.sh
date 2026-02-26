#!/bin/bash
# =============================================================================
# Sony AI Crusoe 集群 - Blender (bpy) 环境一键配置脚本
#
# 用途：在集群上安装 Blender 3.2.2 和 Python 依赖，用于运行 neuralGaufferRendering/scripts 中的 bpy 脚本
#
# 使用方式：
#   ssh mfml1
#   cd /music-shared-disk/group/ct/yiwen/codes/render_objaverse
#   bash SonyAIClusterUtil/setup_bpy_env.sh
#
# 可覆盖的环境变量：
#   PROJ_ROOT   - 项目根目录（默认：当前目录的绝对路径）
#   VENV_DIR    - Python venv 目录（默认：/scratch2/$USER/venv/neural_gaffer）
#   OBJAVERSE_BASE - Objaverse 数据根目录（用于 distribute-general-rendering.py 中的模型路径）
# =============================================================================
set -euo pipefail

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ_ROOT="${PROJ_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
NGR_DIR="${PROJ_ROOT}/neuralGaufferRendering"
VENV_DIR="${VENV_DIR:-/scratch2/$USER/venv/neural_gaffer}"
BLENDER_VERSION="3.2.2"
BLENDER_MAJOR_MINOR="3.2"   # Blender 版本路径用 3.2
BLENDER_DIR="${NGR_DIR}/blender-${BLENDER_VERSION}-linux-x64"

echo "=============================================="
echo "Sony Cluster - Blender (bpy) 环境配置"
echo "=============================================="
echo "项目根目录: $PROJ_ROOT"
echo "Neural Gaffer 目录: $NGR_DIR"
echo "Python venv: $VENV_DIR"
echo "=============================================="

# 检查项目目录
if [[ ! -d "$NGR_DIR" ]]; then
    echo "错误: 未找到 neuralGaufferRendering 目录: $NGR_DIR"
    exit 1
fi

# 1. 安装 Blender
cd "$NGR_DIR"
if [[ -f "${BLENDER_DIR}/blender" ]]; then
    echo "Blender ${BLENDER_VERSION} 已存在，跳过下载"
else
    echo ">>> 下载 Blender ${BLENDER_VERSION}..."
    wget -q --show-progress "https://download.blender.org/release/Blender${BLENDER_MAJOR_MINOR}/blender-${BLENDER_VERSION}-linux-x64.tar.xz" || {
        echo "wget 失败，请检查网络或手动下载"
        exit 1
    }
    echo ">>> 解压 Blender..."
    tar -xf "blender-${BLENDER_VERSION}-linux-x64.tar.xz"
    rm -f "blender-${BLENDER_VERSION}-linux-x64.tar.xz"
fi

# 验证 Blender
"${BLENDER_DIR}/blender" --version
echo ">>> Blender 安装完成"

# 2. 创建 Python venv
echo ">>> 创建 Python 虚拟环境..."
mkdir -p "$(dirname "$VENV_DIR")"
if [[ ! -d "$VENV_DIR" ]]; then
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

# 3. 安装 Python 依赖
echo ">>> 安装 Python 依赖..."
pip install --upgrade pip
if [[ -f "$NGR_DIR/requirements.txt" ]]; then
    pip install -r "$NGR_DIR/requirements.txt"
fi
pip install boto3

# 4. 验证
echo ">>> 验证安装..."
python -c "import tyro, wandb, boto3; print('tyro, wandb, boto3 OK')"
"${BLENDER_DIR}/blender" -b --python-expr "import bpy; print('bpy OK')"

echo ""
echo "=============================================="
echo "配置完成!"
echo "=============================================="
echo ""
echo "激活环境并运行渲染："
echo "  source $VENV_DIR/bin/activate"
echo "  cd $NGR_DIR"
echo ""
echo "单模型测试："
echo "  ./blender-${BLENDER_VERSION}-linux-x64/blender -b -P scripts/blender_script.py -- \\"
echo "    --object_path /path/to/model.glb \\"
echo "    --output_dir /scratch2/\$USER/rendered_test \\"
echo "    --test_light_dir \$LIGHTING_DIR"
echo ""
echo "批量渲染（使用 --input_base_path 指定 Objaverse 根路径）："
echo "  python scripts/distribute-general-rendering.py \\"
echo "    --num_gpus 4 --workers_per_gpu 2 \\"
echo "    --input_models_path /path/to/models.json \\"
echo "    --input_base_path /music-shared-disk/group/ct/yiwen/data/objaverse/hf-objaverse-v1 \\"
echo "    --output_dir /scratch2/\$USER/rendered \\"
echo "    --lighting_dir \$LIGHTING_DIR"
echo ""
echo "详细说明见: SonyAIClusterUtil/bpy_env_setup.md"
echo ""
