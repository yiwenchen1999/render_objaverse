# 3D Scene Rendering on Sony Cluster

## Overview

这套脚本用于在 Sony 集群上运行 `render_3dscenes_dense.py`，渲染由 Polyhaven 模型和 Objaverse 对象组合而成的复杂场景。

## 文件说明

### 核心文件

- **`distribute_render_3dscenes_sony.py`**: 分布式渲染调度器
  - 为每个 GPU 启动多个 Blender worker
  - 自动队列管理和负载均衡
  
- **`run_render_3dscenes_distributed_*.sh`**: Slurm 批处理脚本
  - 每个脚本处理 50 个场景
  - 共 46 个脚本覆盖场景 0-2302

### 辅助脚本

- **`generate_render_3dscenes_scripts.sh`**: 生成所有批处理脚本
- **`submit_all_render_3dscenes.sh`**: 一键提交所有任务

## 快速开始

### 1. 生成渲染脚本

```bash
cd /music-shared-disk/group/ct/yiwen/codes/render_objaverse
bash SonyAIClusterUtil/generate_render_3dscenes_scripts.sh
```

这会生成 46 个脚本:
- `run_render_3dscenes_distributed_0_50.sh`
- `run_render_3dscenes_distributed_50_100.sh`
- ...
- `run_render_3dscenes_distributed_2250_2302.sh`

### 2. 提交渲染任务

**选项 A: 提交所有任务（推荐）**
```bash
bash SonyAIClusterUtil/submit_all_render_3dscenes.sh
```

**选项 B: 提交单个任务**
```bash
sbatch SonyAIClusterUtil/run_render_3dscenes_distributed_0_50.sh
```

**选项 C: 提交特定范围**
```bash
# 提交前 10 个批次 (0-500)
for i in {0..9}; do
  START=$((i*50))
  END=$(((i+1)*50))
  sbatch SonyAIClusterUtil/run_render_3dscenes_distributed_${START}_${END}.sh
done
```

### 3. 监控任务

```bash
# 查看任务队列
squeue -u $USER

# 查看特定任务输出
tail -f slurm_logs/render_scenes_0_50.*.out

# 查看所有错误日志
tail -n 50 slurm_logs/render_scenes_*.err
```

## 配置说明

### 数据路径

- **GLB 文件**: `/music-shared-disk/group/ct/yiwen/data/objaverse/objaverse/hf-objaverse-v1/glbs/`
- **Polyhaven 模型**: `/music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_models`
- **纹理**: `/music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_textures`
- **HDRI 环境贴图**: `/music-shared-disk/group/ct/yiwen/data/objaverse/hdris`
- **输出目录**: `/music-shared-disk/group/ct/yiwen/data/objaverse/rendered_scenes_dense`

### 场景列表

- **场景对象列表**: `test_obj_curated.csv` (2302 个对象)

### 渲染参数

- **Workers per GPU**: 4 个并行 Blender 进程
- **训练视图**: 30 (`--num_views`)
- **测试视图**: 50 (`--num_test_views`)
- **光照配置**:
  - 白色环境光: 1
  - 环境贴图光: 3
  - 白色点光源: 3
  - RGB 点光源: 1
  - 多点光源: 0
  - 区域光: 0

### Slurm 配置

- **Partition**: `sharedp`
- **Account**: `ct`
- **GPU**: 1 个
- **Requeue**: 启用（允许被抢占后重新排队）

## 高级使用

### 修改渲染参数

编辑 `run_render_3dscenes_distributed_*.sh` 中的参数:

```bash
python3 SonyAIClusterUtil/distribute_render_3dscenes_sony.py \
  --workers_per_gpu 6 \          # 增加 workers 提高吞吐量
  --num_views 50 \               # 训练视图数量 (默认: 30)
  --num_test_views 100 \         # 测试视图数量 (默认: 50)
  --num_white_pls 5 \            # 更多点光源
  --num_env_lights 5             # 更多环境光变化
```

### 常用渲染配置预设

**快速预览 (少视图):**
```bash
--num_views 10 --num_test_views 20
```

**标准质量 (默认):**
```bash
--num_views 30 --num_test_views 50
```

**高质量 (多视图):**
```bash
--num_views 50 --num_test_views 100
```

**超高质量 (密集视图):**
```bash
--num_views 100 --num_test_views 200
```

### 测试单个场景

```bash
# 交互式测试
srun --partition=sharedp --account=ct --gres=gpu:1 --pty bash

cd /music-shared-disk/group/ct/yiwen/codes/render_objaverse
export SDL_AUDIODRIVER=dummy

# 渲染单个场景
BLENDER_BIN="neuralGaufferRendering/blender-3.2.2-linux-x64/blender"
$BLENDER_BIN -b -P render_3dscenes_dense.py -- \
  --group_start 0 --group_end 1 \
  --glb_list_path test_obj_curated.csv \
  --glbs_root_path /music-shared-disk/group/ct/yiwen/data/objaverse/objaverse/hf-objaverse-v1/glbs/ \
  --model_lq_dir /music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_models \
  --output_dir ./test_output
```

### 取消任务

```bash
# 取消所有场景渲染任务
scancel -n render_scenes_0_50
scancel -n render_scenes_50_100
# ... 或者
scancel -u $USER --name="render_scenes_*"

# 取消特定任务
scancel <JOB_ID>
```

## 输出结构

每个场景会生成以下文件:

```
rendered_scenes_dense/
└── scene_XXXXX/
    ├── rgb/
    │   ├── 000.png
    │   ├── 001.png
    │   └── ...
    ├── depth/
    ├── normal/
    ├── albedo/
    ├── metadata.json
    └── intrinsics.json
```

## 故障排除

### 问题 1: Blender 未找到

**错误**: `Error: Blender not found`

**解决**:
```bash
# 检查 Blender 路径
ls neuralGaufferRendering/blender-*/blender

# 手动指定路径
python3 SonyAIClusterUtil/distribute_render_3dscenes_sony.py \
  --blender_bin /path/to/blender \
  ...
```

### 问题 2: GLB 文件未找到

**错误**: `FileNotFoundError: GLB not found`

**解决**:
```bash
# 验证 GLB 路径
ls /music-shared-disk/group/ct/yiwen/data/objaverse/objaverse/hf-objaverse-v1/glbs/

# 确保已下载对象
bash SonyAIClusterUtil/download_objaverse_singularity.sh
```

### 问题 3: GPU 利用率低

**解决**: 增加 `--workers_per_gpu`:
```bash
--workers_per_gpu 6  # 从 4 增加到 6
```

### 问题 4: 内存不足

**解决**: 减少并行 workers 或增加内存:
```bash
#SBATCH --mem=64      # 增加内存 (在 .sh 文件中)
--workers_per_gpu 2   # 减少 workers
```

## 性能优化

- **推荐 workers**: 4-6 per GPU (根据 GPU 内存调整)
- **预期时间**: ~5-10 分钟/场景 (取决于复杂度)
- **总预估时间**: 2302 个场景 × 10 分钟 / (46 个并行任务 × 4 workers) ≈ 2-3 小时

## 相关文档

- Polyhaven 模型渲染: `MULTI_WORKER_README.md`
- 集群使用指南: `sonyai_crusoe_day1_quickstart.md`
- Blender 环境设置: `bpy_env_setup.md`
