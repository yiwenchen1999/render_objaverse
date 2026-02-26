# Multi-worker Scene Rendering on Explorer Cluster

使用多 worker 方式加速 `render_3dscenes_dense.py` 在 Explorer 集群上的渲染。

## 快速开始

### 1. 生成所有分布式脚本（20 个范围）

```bash
cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse
bash scripts/generate_all_distributed_scripts.sh
```

生成：
- `scripts/distribute_render_3dscenes_0_50.sh`
- `scripts/distribute_render_3dscenes_50_100.sh`
- ...
- `scripts/distribute_render_3dscenes_950_1000.sh`

### 2. 提交所有任务

```bash
bash scripts/submit_all_distributed_scenes.sh
```

或单独提交：

```bash
sbatch scripts/distribute_render_3dscenes_0_50.sh
sbatch scripts/distribute_render_3dscenes_50_100.sh
# ...
```

### 3. 监控任务

```bash
squeue -u $USER
watch -n 2 squeue -u $USER
```

## 参数说明

- `--workers_per_gpu 4`：每个 GPU 并行 4 个 Blender 进程
- `--num_gpus 1`：每个任务使用 1 块 GPU（a5000 或 h200）
- 每个 worker 渲染单个场景（`--group_start N --group_end N+1`）

## 环境配置

脚本自动加载：
```bash
cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse
source /projects/vig/yiwenc/all_env/blender-env/bin/activate
```

## GPU 选择

修改 sbatch 脚本中的 `#SBATCH --gres=gpu:a5000:1` 为：
- `gpu:a5000:1`：使用 A5000
- `gpu:h200:1`：使用 H200（如果可用）

## 预期加速

- **单 worker**：顺序渲染 50 个场景
- **4 workers**：并行加速 2-4 倍，总时间减少

## 文件结构

```
scripts/
├── distribute_render_3dscenes.py          # 多 worker 调度器
├── distribute_render_3dscenes_0_50.sh     # 场景 0-50
├── distribute_render_3dscenes_50_100.sh   # 场景 50-100
├── ...
├── generate_all_distributed_scripts.sh   # 生成所有脚本
└── submit_all_distributed_scenes.sh       # 提交所有任务
```

## 故障排除

1. **模块未找到**：确保 conda env 已激活
2. **GPU 分配失败**：检查 `sinfo` 查看可用 GPU
3. **内存不足**：降低 `--workers_per_gpu` 为 2
