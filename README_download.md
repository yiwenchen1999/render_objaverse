# 对象下载脚本说明

这个目录包含了用于下载 `test_obj.csv` 文件中所有对象的脚本。

## 文件说明

- `download_test_objects.py` - 主要的Python下载脚本
- `download_test_objects.sh` - SLURM作业脚本，用于在集群上运行
- `run_download.sh` - 本地运行脚本
- `README_download.md` - 本说明文件

## 脚本功能

### 主要特性：
1. **智能检查**: 自动检查已存在的对象，只下载缺失的文件
2. **批量下载**: 每批下载50个对象，避免超时和资源占用
3. **进度监控**: 显示详细的下载进度和统计信息
4. **错误处理**: 处理下载失败、超时等异常情况
5. **临时文件管理**: 自动清理临时文件

### 工作流程：
1. 读取 `test_obj.csv` 文件
2. 检查已存在的对象
3. 创建下载列表JSON文件
4. 分批下载缺失的对象
5. 显示最终统计结果

## 使用方法

### 方法1: 本地运行
```bash
# 直接运行Python脚本
python3 download_test_objects.py

# 或使用shell脚本
./run_download.sh
```

### 方法2: SLURM集群运行
```bash
# 提交到集群
sbatch download_test_objects.sh

# 查看作业状态
squeue -u $USER

# 查看输出
tail -f myjob.download_test_objects.out
```

## 配置参数

### SLURM配置 (download_test_objects.sh):
- **分区**: jiang
- **时间限制**: 24小时
- **内存**: 16GB
- **CPU核心**: 4个
- **输出文件**: `myjob.download_test_objects.out`
- **错误文件**: `myjob.download_test_objects.err`

### 下载参数:
- **批次大小**: 50个对象/批
- **超时时间**: 2小时/批
- **批次间隔**: 5秒

## 输出文件

### 生成的文件：
- `test_objects_download_list.json` - 下载列表JSON文件
- `temp_download_batch_*.json` - 临时批次文件（自动清理）

### 日志信息：
- 对象检查结果
- 下载进度
- 成功/失败统计
- 最终结果汇总

## 示例输出

```
开始处理test_obj.csv中的对象...
检查已存在的对象...
已存在的对象: 15
缺失的对象: 503
总计对象: 518

从 test_obj.csv 读取对象列表...
找到 518 个对象需要下载
下载列表已保存到 test_objects_download_list.json

发现 503 个缺失对象，是否开始下载? (y/n): y

开始批量下载对象，每批 50 个...
总共需要下载 518 个对象

下载批次 1: 对象 1-50
执行下载命令: python download.py --obj_list temp_download_batch_1.json --begin_uid 0 --end_uid 50
批次 1 下载完成!

...

下载完成，进行最终检查...
已存在的对象: 518
仍然缺失的对象: 0

最终结果:
已存在的对象: 518
仍然缺失的对象: 0
下载成功率: 100.0%
```

## 注意事项

1. **依赖文件**: 确保 `download.py` 和 `test_obj.csv` 文件存在
2. **磁盘空间**: 确保有足够的磁盘空间存储下载的GLB文件
3. **网络连接**: 下载过程需要稳定的网络连接
4. **时间限制**: 大量对象下载可能需要较长时间
5. **资源使用**: 在集群上运行时注意资源限制

## 故障排除

### 常见问题：
1. **下载失败**: 检查网络连接和objaverse服务状态
2. **超时错误**: 减少批次大小或增加超时时间
3. **权限错误**: 确保有写入目标目录的权限
4. **内存不足**: 减少批次大小或增加内存分配

### 手动恢复：
如果下载中断，可以重新运行脚本，它会自动跳过已存在的文件。
