# Blender (bpy) 脚本环境配置 - Sony AI Crusoe 集群

本指南帮助你在 Sony AI Crusoe 集群上配置环境，以运行 `neuralGaufferRendering/scripts/` 下的 Blender 渲染脚本（如 `blender_script.py`、`distribute-general-rendering.py`）。

## 前置知识

- **bpy**：Blender 内置的 Python 模块，需通过 Blender 的 Python 运行（`blender -b -P script.py`）
- **distribute-general-rendering.py**：调度脚本，用系统 Python 运行，内部会启动多个 Blender 进程进行渲染
- **Blender**：需在集群上单独安装（项目用 Blender 3.2.2）

## 1. 登录与基础配置

```bash
# 登录集群（推荐使用 mfml1）
ssh mfml1

# 如未配置，在 ~/.bashrc 添加 Slurm 工具（参考 sonyai_crusoe_day1_quickstart.md）
export SLURM_USER_TOOL_ROOT=/usr/local/share/slurm-user/
if [ -d $SLURM_USER_TOOL_ROOT ]; then
  export PATH="${SLURM_USER_TOOL_ROOT}:$PATH"
  source ${SLURM_USER_TOOL_ROOT}/slurm-crusoe.bash_profile
fi

source ~/.bashrc
```

## 2. 项目路径与存储建议

建议将项目放在共享盘：

```bash
# 项目根目录（根据实际情况调整）
export PROJ_ROOT=/music-shared-disk/group/ct/yiwen/codes/render_objaverse
export NGR_DIR=$PROJ_ROOT/neuralGaufferRendering

# 数据目录
export DATA_ROOT=/music-shared-disk/group/ct/yiwen/data
export OBJAVERSE_BASE=$DATA_ROOT/objaverse/hf-objaverse-v1   # Objaverse 模型根目录
export LIGHTING_DIR=$DATA_ROOT/light_probes_selected_exr     # 环境光 HDR/EXR
```

## 3. 安装 Blender 3.2.2

在 `neuralGaufferRendering` 目录下安装 Blender（与 `distribute-general-rendering.py` 中的路径一致）：

```bash
cd $NGR_DIR

# 下载并解压 Blender 3.2.2
wget https://download.blender.org/release/Blender3.2/blender-3.2.2-linux-x64.tar.xz
tar -xf blender-3.2.2-linux-x64.tar.xz
rm blender-3.2.2-linux-x64.tar.xz

# 验证
./blender-3.2.2-linux-x64/blender --version
# 应输出: Blender 3.2.2
```

## 4. 创建 Python 环境

### 方案 A：Python venv

`distribute-general-rendering.py` 需要 `tyro`、`wandb`、`boto3` 等依赖，用 venv 管理：

```bash
# 在 scratch 下创建 venv（I/O 更快）
export VENV_DIR=/scratch2/$USER/venv/neural_gaffer
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# 升级 pip 并安装依赖
pip install --upgrade pip
pip install -r $NGR_DIR/requirements.txt
pip install boto3

# 验证
python -c "import tyro, wandb, boto3; print('OK')"
```

### 方案 B：Singularity 容器（推荐集群标准流程）

使用集群已有的 PyTorch SIF，将 Python 依赖安装到 `--target` 目录，通过 bind 挂载访问项目和 Blender：

```bash
# 环境变量
export PROJ_ROOT=/music-shared-disk/group/ct/yiwen/codes/render_objaverse
export NGR_DIR=$PROJ_ROOT/neuralGaufferRendering
export PY_SITE=/scratch2/$USER/ng_bpy_py          # Python 包安装目标
export SIF_DIR=/scratch2/$USER/singularity_images
export SIF=$SIF_DIR/pytorch_24.01-py3.sif         # 或你已有的 PyTorch SIF
export BIND="-B /group2,/scratch2,/data,/music-shared-disk"
export PIP_CACHE_DIR=/scratch2/$USER/cache/pip

mkdir -p "$PY_SITE" "$PIP_CACHE_DIR"

# 在容器内安装 Python 依赖到 PY_SITE
singularity exec --nv $BIND $SIF bash -lc "
  python3 -m pip install -U pip wheel setuptools --cache-dir $PIP_CACHE_DIR
"
singularity exec --nv $BIND $SIF bash -lc "
  python3 -m pip install -r $NGR_DIR/requirements.txt boto3 --target $PY_SITE --cache-dir $PIP_CACHE_DIR
"

# 验证
singularity exec --nv $BIND $SIF bash -lc "
  export PYTHONPATH=$PY_SITE:\$PYTHONPATH
  python3 -c 'import tyro, wandb, boto3; print(\"OK\")'
"
```

**说明**：
- Blender 安装在项目目录（见第 3 节），通过 `-B /music-shared-disk` 挂载后，容器内可直接运行 `$NGR_DIR/blender-3.2.2-linux-x64/blender`。`distribute-general-rendering.py` 会在容器内启动 Blender 子进程。
- SIF 镜像需提前准备（如 `pytorch_24.01-py3.sif` 放在 `/scratch2/$USER/singularity_images/`）。若尚无镜像，可参考 README 中的 Singularity 教程或询问集群管理员获取共享镜像。

## 5. Objaverse 模型路径配置

`distribute-general-rendering.py` 支持三种方式指定 Objaverse 根路径（JSON 中为相对路径）：

1. **命令行参数**（推荐）：`--input_base_path /music-shared-disk/group/ct/yiwen/data/objaverse/hf-objaverse-v1`
2. **环境变量**：`export OBJAVERSE_BASE=/music-shared-disk/group/ct/yiwen/data/objaverse/hf-objaverse-v1`
3. **默认值**：未指定时使用原始硬编码路径（需手动改代码）

## 6. 环境变量（可选，建议写入 ~/.bashrc）

```bash
# bpy / Neural Gaffer 渲染
export PROJ_ROOT=/music-shared-disk/group/ct/yiwen/codes/render_objaverse
export NGR_DIR=$PROJ_ROOT/neuralGaufferRendering
export OBJAVERSE_BASE=/music-shared-disk/group/ct/yiwen/data/objaverse/hf-objaverse-v1
export LIGHTING_DIR=/music-shared-disk/group/ct/yiwen/data/light_probes_selected_exr
export VENV_DIR=/scratch2/$USER/venv/neural_gaffer

# Pip 缓存（加快安装）
export PIP_CACHE_DIR=/scratch2/$USER/cache/pip
```

## 7. 运行渲染

### 7.1 快速测试（srun）

**使用 venv：**
```bash
cd $NGR_DIR
source $VENV_DIR/bin/activate

srun --partition=ct --account=ct --gres=gpu:1 --job-name=bpy_test \
  bash -lc "
    cd $NGR_DIR && source $VENV_DIR/bin/activate &&
    CUDA_VISIBLE_DEVICES=0 ./blender-3.2.2-linux-x64/blender -b -P scripts/blender_script.py -- \
      --object_path /path/to/one/model.glb \
      --output_dir /scratch2/\$USER/rendered_test \
      --test_light_dir $LIGHTING_DIR
  "
```

**使用 Singularity：**
```bash
SIF=/scratch2/$USER/singularity_images/pytorch_24.01-py3.sif
BIND="-B /group2,/scratch2,/data,/music-shared-disk"
PY_SITE=/scratch2/$USER/ng_bpy_py

srun --partition=ct --account=ct --gres=gpu:1 --job-name=bpy_test \
  singularity exec --nv $BIND $SIF bash -lc "
    cd $NGR_DIR &&
    export PYTHONPATH=$PY_SITE:\$PYTHONPATH &&
    CUDA_VISIBLE_DEVICES=0 ./blender-3.2.2-linux-x64/blender -b -P scripts/blender_script.py -- \
      --object_path /path/to/one/model.glb \
      --output_dir /scratch2/\$USER/rendered_test \
      --test_light_dir $LIGHTING_DIR
  "
```

### 7.2 批量渲染（sbatch）

**使用 venv：**
```bash
#!/bin/bash
#SBATCH --partition=ct,sharedp
#SBATCH --account=ct
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:4
#SBATCH --job-name=ng_render
#SBATCH --output=slurm_logs/%x.%j.out
#SBATCH --error=slurm_logs/%x.%j.err
#SBATCH --requeue

PROJ_ROOT=/music-shared-disk/group/ct/yiwen/codes/render_objaverse
NGR_DIR=$PROJ_ROOT/neuralGaufferRendering
VENV_DIR=/scratch2/$USER/venv/neural_gaffer

mkdir -p slurm_logs
cd $NGR_DIR
source $VENV_DIR/bin/activate

python scripts/distribute-general-rendering.py \
  --num_gpus 4 --workers_per_gpu 2 \
  --input_models_path /path/to/filtered_object_list.json \
  --input_base_path /music-shared-disk/group/ct/yiwen/data/objaverse/hf-objaverse-v1 \
  --output_dir /scratch2/$USER/rendered_output \
  --lighting_dir $LIGHTING_DIR
```

**使用 Singularity：**
```bash
#!/bin/bash
#SBATCH --partition=ct,sharedp
#SBATCH --account=ct
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:4
#SBATCH --job-name=ng_render
#SBATCH --output=slurm_logs/%x.%j.out
#SBATCH --error=slurm_logs/%x.%j.err
#SBATCH --requeue

PROJ_ROOT=/music-shared-disk/group/ct/yiwen/codes/render_objaverse
NGR_DIR=$PROJ_ROOT/neuralGaufferRendering
SIF=/scratch2/$USER/singularity_images/pytorch_24.01-py3.sif
BIND="-B /group2,/scratch2,/data,/music-shared-disk"
PY_SITE=/scratch2/$USER/ng_bpy_py

mkdir -p slurm_logs
cd $NGR_DIR

singularity exec --nv $BIND $SIF bash -lc "
  export PYTHONPATH=$PY_SITE:\$PYTHONPATH
  cd $NGR_DIR
  python scripts/distribute-general-rendering.py \
    --num_gpus 4 --workers_per_gpu 2 \
    --input_models_path /path/to/filtered_object_list.json \
    --input_base_path /music-shared-disk/group/ct/yiwen/data/objaverse/hf-objaverse-v1 \
    --output_dir /scratch2/\$USER/rendered_output \
    --lighting_dir /music-shared-disk/group/ct/yiwen/data/light_probes_selected_exr
"
```

提交：

```bash
sbatch run_rendering.sh
```

## 8. 其他 bpy 脚本

- **resize_environment_map.py**：需用系统 Python 运行，依赖 skylibs；需修改其中的 `input_dir` / `output_dir`
- **preprocess_rendered_image.py**：预处理渲染图，普通 Python
- **preprocess_environment_map.py**：预处理环境光，普通 Python

这些脚本不依赖 Blender，只需在 venv 中安装 `requirements.txt` 和 skylibs 即可。

## 9. 故障排除

### Blender 找不到或报错

```bash
# 确认 Blender 路径
ls $NGR_DIR/blender-3.2.2-linux-x64/blender
$NGR_DIR/blender-3.2.2-linux-x64/blender --version
```

### SSL 证书问题（如 wget/Blender 下载失败）

```bash
# 如有权限，可尝试更新 CA 证书（通常由管理员处理）
# export SSL_CERT_DIR=/etc/ssl/certs
```

### 无 X 服务器

Blender 使用 `-b`（headless）模式，无需显示器。`blender -b -P script.py` 可在无 X 环境下运行。

### 分区与资源

- 使用 GPU 分区（如 `ct`、`sharedp`）以加速 Cycles 渲染
- 团队分区 `ct` 优先；`sharedp` 可能被抢占，需做好 checkpoint/断点续跑

## 10. 快速参考

**venv 方式：**
```bash
ssh mfml1
source /scratch2/$USER/venv/neural_gaffer/bin/activate
cd /music-shared-disk/group/ct/yiwen/codes/render_objaverse/neuralGaufferRendering

# 单模型
./blender-3.2.2-linux-x64/blender -b -P scripts/blender_script.py -- \
  --object_path /path/to/model.glb --output_dir /scratch2/$USER/out --test_light_dir $LIGHTING_DIR

# 批量
python scripts/distribute-general-rendering.py --num_gpus 4 --workers_per_gpu 2 \
  --input_models_path /path/to/models.json --input_base_path /music-shared-disk/group/ct/yiwen/data/objaverse/hf-objaverse-v1 \
  --output_dir /scratch2/$USER/out --lighting_dir $LIGHTING_DIR
```

**Singularity 方式：**
```bash
ssh mfml1
SIF=/scratch2/$USER/singularity_images/pytorch_24.01-py3.sif
BIND="-B /group2,/scratch2,/data,/music-shared-disk"
PY_SITE=/scratch2/$USER/ng_bpy_py

# 批量（在容器内执行）
singularity exec --nv $BIND $SIF bash -lc "
  export PYTHONPATH=$PY_SITE:\$PYTHONPATH
  cd /music-shared-disk/group/ct/yiwen/codes/render_objaverse/neuralGaufferRendering
  python scripts/distribute-general-rendering.py --num_gpus 4 --workers_per_gpu 2 \
    --input_models_path /path/to/models.json --input_base_path /music-shared-disk/group/ct/yiwen/data/objaverse/hf-objaverse-v1 \
    --output_dir /scratch2/\$USER/out --lighting_dir /music-shared-disk/group/ct/yiwen/data/light_probes_selected_exr
"
```
