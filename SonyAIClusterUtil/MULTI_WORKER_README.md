# Multi-worker Polyhaven Rendering

使用多 worker 方式提高单 GPU 渲染吞吐（减少 CPU/IO 等待时间）。

## 原理

- 单个 GPU 同时运行多个 Blender 进程（通过 `CUDA_VISIBLE_DEVICES`）
- 当一个进程在加载模型/写文件时，其他进程可以继续 GPU 渲染
- 通常能提升 2-4 倍总吞吐

## 用法

### 1. 测试运行（4 个模型，4 个 worker）

```bash
# 在计算节点上（sbash 或 srun 后）
bash SonyAIClusterUtil/run_render_3dmodels_dense_polyhaven_distributed_test.sh
```

同时观察 GPU 利用率：

```bash
# 另一个终端
watch -n 1 nvidia-smi
```

### 2. 批量提交（240 模型，4 组 x 4 workers）

**一键提交所有 4 个任务（0-60, 60-120, 120-180, 180-240）：**

```bash
cd /music-shared-disk/group/ct/yiwen/codes/render_objaverse
bash SonyAIClusterUtil/submit_all_distributed_polyhaven.sh
```

**或单独提交：**

```bash
sbatch SonyAIClusterUtil/run_render_3dmodels_dense_polyhaven_distributed_0_60.sh
sbatch SonyAIClusterUtil/run_render_3dmodels_dense_polyhaven_distributed_60_120.sh
sbatch SonyAIClusterUtil/run_render_3dmodels_dense_polyhaven_distributed_120_180.sh
sbatch SonyAIClusterUtil/run_render_3dmodels_dense_polyhaven_distributed_180_240.sh
```

### 3. 手动调用

```bash
python3 SonyAIClusterUtil/distribute_render_polyhaven.py \
  --num_gpus 1 \
  --workers_per_gpu 4 \
  --group_start 0 \
  --group_end 60 \
  --model_list_path assets/object_ids/polyhaven_models_train.json \
  --output_dir /music-shared-disk/group/ct/yiwen/data/objaverse/rendered_dense_polyhaven \
  --cycles_tile_size 512
```

## 参数说明

- `--workers_per_gpu`：每个 GPU 的并发 Blender 进程数（推荐 2-4）
- `--num_gpus`：使用的 GPU 数量（单卡任务设为 1）
- `--cycles_tile_size`：Cycles tile 大小（512×512 渲染时最大 512）
- `--group_start` / `--group_end`：模型列表的范围

## 依赖

无额外依赖，使用 Python 标准库。

## 注意事项

1. **内存**：多 worker 会增加内存占用（每个 Blender 进程约 2-4GB）
2. **显存**：GPU 显存由多个进程共享，H100 80GB 通常没问题
3. **worker 数量**：建议从 2 开始测试，逐步增加到 4；过多会导致内存/显存溢出
4. **输出冲突**：脚本会自动跳过已渲染的模型（检查 `done.txt`）

## 对比单 worker

- **单 worker**（原始 sbatch）：顺序渲染，GPU 利用率 5-20%
- **多 worker**（distributed）：并发渲染，GPU 利用率 40-80%，总时间减少 2-4 倍
