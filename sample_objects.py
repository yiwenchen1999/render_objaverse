#!/usr/bin/env python3
"""
脚本用于从两个不同的数据源中分别采样20个对象并复制到指定目录
"""

import json
import csv
import random
import os
import shutil
import subprocess
import sys
from pathlib import Path

def create_directories():
    """创建目标目录"""
    dirs = ['./filtered_from_json', './filtered_from_csv']
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"创建目录: {dir_path}")

def download_missing_objects(missing_uids, source_type="json"):
    """下载缺失的对象"""
    if not missing_uids:
        return True
    
    print(f"发现 {len(missing_uids)} 个缺失的对象，开始下载...")
    
    # 创建临时文件来存储需要下载的UID
    temp_file = f"temp_download_{source_type}.json"
    temp_data = {uid: f"glbs/000-000/{uid}.glb" for uid in missing_uids}
    
    with open(temp_file, 'w') as f:
        json.dump(temp_data, f)
    
    try:
        # 运行下载脚本
        cmd = [
            sys.executable, "download.py",
            "--obj_list", temp_file,
            "--begin_uid", "0",
            "--end_uid", str(len(missing_uids))
        ]
        
        print(f"执行下载命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)  # 1小时超时
        
        if result.returncode == 0:
            print("下载完成!")
            return True
        else:
            print(f"下载失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("下载超时!")
        return False
    except Exception as e:
        print(f"下载过程中出现错误: {e}")
        return False
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)

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
    
    # 第一遍检查：找出缺失的文件
    missing_uids = []
    for key in sampled_keys:
        relative_path = data[key]  # 例如: "glbs/000-019/2d0dcf63909f40b0b4546726606414e7.glb"
        relative_path = relative_path.replace('glbs/', '')
        source_path = os.path.join(source_base, relative_path)
        if not os.path.exists(source_path):
            missing_uids.append(key)
    
    # 如果有缺失的文件，尝试下载
    if missing_uids:
        print(f"发现 {len(missing_uids)} 个缺失的文件，尝试下载...")
        download_success = download_missing_objects(missing_uids, "json")
        if not download_success:
            print("下载失败，继续处理现有文件...")
    
    # 第二遍：复制文件
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
    
    # 第一遍检查：找出缺失的文件
    missing_uids = []
    for row in sampled_rows:
        if len(row) >= 2:
            folder = row[0]  # 例如: "000-001"
            uid = row[1]     # 例如: "112c059282cf4511a01fd27211edcae8"
            
            # 构建源文件路径
            source_path = os.path.join(source_base, folder, f"{uid}.glb")
            if not os.path.exists(source_path):
                missing_uids.append(uid)
    
    # 如果有缺失的文件，尝试下载
    if missing_uids:
        print(f"发现 {len(missing_uids)} 个缺失的文件，尝试下载...")
        download_success = download_missing_objects(missing_uids, "csv")
        if not download_success:
            print("下载失败，继续处理现有文件...")
    
    # 第二遍：复制文件
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

def check_dependencies():
    """检查依赖文件是否存在"""
    required_files = ["download.py", "all_objaverse_filtered_data.json", "filtered_uids.csv"]
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"错误: 缺少以下必需文件: {', '.join(missing_files)}")
        return False
    
    return True

def main():
    """主函数"""
    print("开始取前20个对象...")
    
    # 检查依赖文件
    if not check_dependencies():
        return
    
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
    print(f"取前20个对象完成!")
    print(f"从JSON复制了 {json_count} 个文件")
    print(f"从CSV复制了 {csv_count} 个文件")
    print(f"总计复制了 {json_count + csv_count} 个文件")

if __name__ == "__main__":
    main()
