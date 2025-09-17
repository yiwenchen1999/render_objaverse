# 对象采样脚本说明

这个脚本用于从两个不同的数据源中分别采样20个3D对象并复制到指定目录。

## 文件说明

- `sample_objects.py`: 主要的Python采样脚本
- `run_sampling.sh`: 可执行的shell脚本，用于运行采样程序
- `README_sampling.md`: 本说明文件

## 数据源

1. **JSON文件**: `all_objaverse_filtered_data.json`
   - 格式: `{"uid": "glbs/folder/uid.glb", ...}`
   - 采样结果保存到: `./filtered_from_json/`

2. **CSV文件**: `filtered_uids.csv`
   - 格式: `folder,uid` (例如: `000-001,112c059282cf4511a01fd27211edcae8`)
   - 采样结果保存到: `./filtered_from_csv/`

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

脚本会创建以下目录并复制采样的GLB文件:

- `./filtered_from_json/`: 从JSON文件采样的20个对象
- `./filtered_from_csv/`: 从CSV文件采样的20个对象

每个文件会以对应的UID命名，例如: `112c059282cf4511a01fd27211edcae8.glb`

## 注意事项

1. 确保源数据目录 `/projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/` 存在且可访问
2. 脚本使用固定随机种子 (42) 以确保结果可重现
3. 如果源文件不存在，脚本会显示警告但继续处理其他文件
4. 脚本会自动创建目标目录

## 示例输出

```
开始采样对象...
创建目录: ./filtered_from_json
创建目录: ./filtered_from_csv
从 all_objaverse_filtered_data.json 中采样 20 个对象...
复制: glbs/000-019/2d0dcf63909f40b0b4546726606414e7.glb -> 2d0dcf63909f40b0b4546726606414e7.glb
...
从JSON成功复制了 20 个文件到 ./filtered_from_json
--------------------------------------------------
从 filtered_uids.csv 中采样 20 个对象...
复制: 000-001/112c059282cf4511a01fd27211edcae8.glb -> 112c059282cf4511a01fd27211edcae8.glb
...
从CSV成功复制了 20 个文件到 ./filtered_from_csv
--------------------------------------------------
采样完成!
从JSON复制了 20 个文件
从CSV复制了 20 个文件
总计复制了 40 个文件
```
