# 对象采样脚本说明

这个脚本用于从两个不同的数据源中分别取前20个3D对象并复制到指定目录。

## 文件说明

- `sample_objects.py`: 主要的Python采样脚本
- `run_sampling.sh`: 可执行的shell脚本，用于运行采样程序
- `README_sampling.md`: 本说明文件

## 数据源

1. **JSON文件**: `all_objaverse_filtered_data.json`
   - 格式: `{"uid": "glbs/folder/uid.glb", ...}`
   - 取前20个对象保存到: `./filtered_from_json/`

2. **CSV文件**: `filtered_uids.csv`
   - 格式: `folder,uid` (例如: `000-001,112c059282cf4511a01fd27211edcae8`)
   - 取前20个对象保存到: `./filtered_from_csv/`

## 源数据路径

GLB模型文件位于: `/projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/`

目录结构:
```
/projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/
├── 000-001/
│   ├── 112c059282cf4511a01fd27211edcae8.glb
│   └── ...
├── 000-002/
│   └── ...
└── ...
```

## 使用方法

### 方法1: 使用shell脚本 (推荐)
```bash
./run_sampling.sh
```

### 方法2: 直接运行Python脚本
```bash
python3 sample_objects.py
```

## 输出

脚本会创建以下目录并复制前20个GLB文件:

- `./filtered_from_json/`: 从JSON文件取前20个对象
- `./filtered_from_csv/`: 从CSV文件取前20个对象

每个文件会以对应的UID命名，例如: `112c059282cf4511a01fd27211edcae8.glb`

## 注意事项

1. 确保源数据目录 `/projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/` 存在且可访问
2. 脚本按顺序取前20个对象，结果可重现
3. **自动下载功能**: 如果源文件不存在，脚本会自动尝试下载缺失的模型文件
4. 脚本会自动创建目标目录
5. 下载过程可能需要较长时间，请耐心等待
6. 确保有足够的磁盘空间用于下载和存储模型文件

## 示例输出

```
开始取前20个对象...
创建目录: ./filtered_from_json
创建目录: ./filtered_from_csv
从 all_objaverse_filtered_data.json 中取前 20 个对象...
发现 5 个缺失的文件，尝试下载...
执行下载命令: python download.py --obj_list temp_download_json.json --begin_uid 0 --end_uid 5
下载完成!
复制: glbs/000-019/2d0dcf63909f40b0b4546726606414e7.glb -> 2d0dcf63909f40b0b4546726606414e7.glb
...
从JSON成功复制了 20 个文件到 ./filtered_from_json
--------------------------------------------------
从 filtered_uids.csv 中取前 20 个对象...
发现 3 个缺失的文件，尝试下载...
执行下载命令: python download.py --obj_list temp_download_csv.json --begin_uid 0 --end_uid 3
下载完成!
复制: 000-001/112c059282cf4511a01fd27211edcae8.glb -> 112c059282cf4511a01fd27211edcae8.glb
...
从CSV成功复制了 20 个文件到 ./filtered_from_csv
--------------------------------------------------
取前20个对象完成!
从JSON复制了 20 个文件
从CSV复制了 20 个文件
总计复制了 40 个文件
```
