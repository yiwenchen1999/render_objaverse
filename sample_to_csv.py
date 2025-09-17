#!/usr/bin/env python3
"""
脚本用于从JSON文件中采样500个对象并添加到CSV文件中
"""

import json
import csv
import random
import os

def sample_from_json_to_csv(json_file, csv_file, num_samples=500):
    """从JSON文件中采样对象并添加到CSV文件"""
    print(f"从 {json_file} 中采样 {num_samples} 个对象...")
    
    # 读取JSON文件
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # 获取所有键
    all_keys = list(data.keys())
    print(f"JSON文件中共有 {len(all_keys)} 个对象")
    
    # 随机采样
    random.seed(42)  # 设置随机种子以确保可重现性
    sampled_keys = random.sample(all_keys, min(num_samples, len(all_keys)))
    
    print(f"采样了 {len(sampled_keys)} 个对象")
    
    # 读取现有CSV文件内容
    existing_entries = []
    if os.path.exists(csv_file):
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2 and row[0].strip() and row[1].strip():
                    existing_entries.append((row[0].strip(), row[1].strip()))
        print(f"现有CSV文件中有 {len(existing_entries)} 个条目")
    
    # 准备新条目
    new_entries = []
    for key in sampled_keys:
        relative_path = data[key]  # 例如: "glbs/000-019/2d0dcf63909f40b0b4546726606414e7.glb"
        
        # 从路径中提取文件夹名
        # 路径格式: "glbs/000-019/uid.glb"
        path_parts = relative_path.split('/')
        if len(path_parts) >= 3:
            folder = path_parts[1]  # 例如: "000-019"
            uid = key
            new_entries.append((folder, uid))
        else:
            print(f"警告: 无法解析路径 {relative_path}")
    
    # 合并现有条目和新条目
    all_entries = existing_entries + new_entries
    
    # 去重（基于UID）
    seen_uids = set()
    unique_entries = []
    for folder, uid in all_entries:
        if uid not in seen_uids:
            seen_uids.add(uid)
            unique_entries.append((folder, uid))
    
    print(f"去重后共有 {len(unique_entries)} 个条目")
    print(f"新增了 {len(unique_entries) - len(existing_entries)} 个条目")
    
    # 写入CSV文件
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        for folder, uid in unique_entries:
            writer.writerow([folder, uid])
    
    print(f"成功将数据写入 {csv_file}")
    
    # 显示一些示例
    print("\n新增的条目示例:")
    for i, (folder, uid) in enumerate(new_entries[:5]):
        print(f"  {folder},{uid}")
    if len(new_entries) > 5:
        print(f"  ... 还有 {len(new_entries) - 5} 个条目")

def main():
    """主函数"""
    json_file = "all_objaverse_filtered_data.json"
    csv_file = "test_obj.csv"
    
    # 检查JSON文件是否存在
    if not os.path.exists(json_file):
        print(f"错误: 找不到文件 {json_file}")
        return
    
    print("开始从JSON文件采样对象到CSV文件...")
    sample_from_json_to_csv(json_file, csv_file, 500)
    print("采样完成!")

if __name__ == "__main__":
    main()
