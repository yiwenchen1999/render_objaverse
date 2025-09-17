#!/usr/bin/env python3
"""
脚本用于从两个不同的数据源中分别采样20个对象并复制到指定目录
"""

import json
import csv
import random
import os
import shutil
from pathlib import Path

def create_directories():
    """创建目标目录"""
    dirs = ['./filtered_from_json', './filtered_from_csv']
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"创建目录: {dir_path}")

def sample_from_json(json_file, num_samples=20):
    """从JSON文件中采样对象"""
    print(f"从 {json_file} 中取前 {num_samples} 个对象...")
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # 取前N个对象
    all_keys = list(data.keys())
    sampled_keys = all_keys[:min(num_samples, len(all_keys))]
    
    source_base = "/projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/"
    target_dir = "./filtered_from_json"
    
    copied_count = 0
    for key in sampled_keys:
        relative_path = data[key]  # 例如: "glbs/000-019/2d0dcf63909f40b0b4546726606414e7.glb"
        source_path = os.path.join(source_base, relative_path)
        target_path = os.path.join(target_dir, f"{key}.glb")
        
        if os.path.exists(source_path):
            shutil.copy2(source_path, target_path)
            copied_count += 1
            print(f"复制: {relative_path} -> {key}.glb")
        else:
            print(f"警告: 源文件不存在 {source_path}")
    
    print(f"从JSON成功复制了 {copied_count} 个文件到 {target_dir}")
    return copied_count

def sample_from_csv(csv_file, num_samples=20):
    """从CSV文件中采样对象"""
    print(f"从 {csv_file} 中取前 {num_samples} 个对象...")
    
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    # 取前N个对象
    sampled_rows = rows[:min(num_samples, len(rows))]
    
    source_base = "/projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/"
    target_dir = "./filtered_from_csv"
    
    copied_count = 0
    for row in sampled_rows:
        if len(row) >= 2:
            folder = row[0]  # 例如: "000-001"
            uid = row[1]     # 例如: "112c059282cf4511a01fd27211edcae8"
            
            # 构建源文件路径
            source_path = os.path.join(source_base, folder, f"{uid}.glb")
            target_path = os.path.join(target_dir, f"{uid}.glb")
            
            if os.path.exists(source_path):
                shutil.copy2(source_path, target_path)
                copied_count += 1
                print(f"复制: {folder}/{uid}.glb -> {uid}.glb")
            else:
                print(f"警告: 源文件不存在 {source_path}")
    
    print(f"从CSV成功复制了 {copied_count} 个文件到 {target_dir}")
    return copied_count

def main():
    """主函数"""
    print("开始取前20个对象...")
    
    # 创建目标目录
    create_directories()
    
    # 从JSON文件采样
    json_file = "all_objaverse_filtered_data.json"
    if os.path.exists(json_file):
        json_count = sample_from_json(json_file, 20)
    else:
        print(f"错误: 找不到文件 {json_file}")
        json_count = 0
    
    print("-" * 50)
    
    # 从CSV文件采样
    csv_file = "filtered_uids.csv"
    if os.path.exists(csv_file):
        csv_count = sample_from_csv(csv_file, 20)
    else:
        print(f"错误: 找不到文件 {csv_file}")
        csv_count = 0
    
    print("-" * 50)
    print(f"采样完成!")
    print(f"从JSON复制了 {json_count} 个文件")
    print(f"从CSV复制了 {csv_count} 个文件")
    print(f"总计复制了 {json_count + csv_count} 个文件")

if __name__ == "__main__":
    main()
