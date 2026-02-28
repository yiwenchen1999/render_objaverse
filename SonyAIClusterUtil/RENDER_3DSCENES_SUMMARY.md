# Sony 集群 - 3D 场景渲染系统

## ✅ 已创建的文件

### 核心文件
1. **`distribute_render_3dscenes_sony.py`** - Python 分布式调度器
2. **`run_render_3dscenes_distributed_*.sh`** - 46 个 Slurm 批处理脚本 (0-2302 场景)
3. **`generate_render_3dscenes_scripts.sh`** - 脚本生成器
4. **`submit_all_render_3dscenes.sh`** - 批量提交工具
5. **`RENDER_3DSCENES_README.md`** - 完整文档

## 🚀 快速开始

### 在 Sony 集群上运行

```bash
# 1. SSH 到集群
ssh mfml1

# 2. 进入项目目录
cd /music-shared-disk/group/ct/yiwen/codes/render_objaverse

# 3. 生成所有渲染脚本 (46 个)
bash SonyAIClusterUtil/generate_render_3dscenes_scripts.sh

# 4. 提交所有任务
bash SonyAIClusterUtil/submit_all_render_3dscenes.sh

# 5. 监控任务
squeue -u $USER
tail -f slurm_logs/render_scenes_*.out
```

## 📊 配置概览

| 参数 | 值 |
|------|-----|
| **总场景数** | 2,302 (来自 test_obj_curated.csv) |
| **批次数** | 46 (每批次 ~50 场景) |
| **Workers/GPU** | 4 个并行 Blender 进程 |
| **GPU 类型** | H100 (sharedp partition) |
| **GLB 路径** | `/music-shared-disk/.../hf-objaverse-v1/glbs/` |
| **输出路径** | `/music-shared-disk/.../rendered_scenes_dense/` |

## 🎨 光照配置

- 白色环境光: 1
- 环境贴图光: 3  
- 白色点光源: 3
- RGB 点光源: 1
- 多点光源: 0
- 区域光: 0

## 📁 数据路径

```bash
GLB 对象:     /music-shared-disk/group/ct/yiwen/data/objaverse/objaverse/hf-objaverse-v1/glbs/
Polyhaven:    /music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_models
纹理:         /music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_textures
HDRI:         /music-shared-disk/group/ct/yiwen/data/objaverse/hdris
输出:         /music-shared-disk/group/ct/yiwen/data/objaverse/rendered_scenes_dense
```

## ⚙️ 脚本列表

生成的 46 个批处理脚本:

```
run_render_3dscenes_distributed_0_50.sh
run_render_3dscenes_distributed_50_100.sh
run_render_3dscenes_distributed_100_150.sh
...
run_render_3dscenes_distributed_2200_2250.sh
run_render_3dscenes_distributed_2250_2302.sh
```

## 🔧 自定义参数

编辑任意 `.sh` 文件修改参数:

```bash
--workers_per_gpu 6          # 增加并行度
--num_white_pls 5            # 更多点光源
--num_env_lights 5           # 更多环境光变化
```

## 📈 性能估算

- **单场景时间**: ~5-10 分钟
- **并行任务数**: 46 个 GPU × 4 workers = 184 个并行进程
- **总预估时间**: 2302 场景 / 184 并行 × 7.5 分钟 ≈ **1.5-2 小时**

## 🛠️ 常用命令

```bash
# 查看任务状态
squeue -u $USER

# 取消所有场景渲染
scancel -u $USER --name="render_scenes_*"

# 查看特定任务输出
tail -f slurm_logs/render_scenes_100_150.*.out

# 统计已完成场景
find /music-shared-disk/.../rendered_scenes_dense/ -mindepth 1 -maxdepth 1 -type d | wc -l
```

## 📚 相关文档

- **完整文档**: `SonyAIClusterUtil/RENDER_3DSCENES_README.md`
- **Polyhaven 渲染**: `SonyAIClusterUtil/MULTI_WORKER_README.md`
- **集群快速入门**: `SonyAIClusterUtil/sonyai_crusoe_day1_quickstart.md`
- **下载脚本**: `SonyAIClusterUtil/download_objaverse_singularity.sh`

## ✨ 特点

✅ 分布式多 worker 架构 (4 workers/GPU)  
✅ 自动队列管理和负载均衡  
✅ 支持任务抢占后重新排队 (--requeue)  
✅ 自动检测 Blender 路径  
✅ 完整的错误处理和日志记录  
✅ 灵活的参数配置  

---

**创建时间**: 2026-02-25  
**总文件数**: 51 (46 个批处理脚本 + 5 个辅助文件)
