#!/usr/bin/env python3
"""
脚本用于下载test_obj.csv文件中的所有对象
"""

import csv
import os
import sys
import subprocess
import json
import time

def create_download_list_from_csv(csv_file, output_json_file):
    """从CSV文件创建下载列表"""
    print(f"从 {csv_file} 读取对象列表...")
    
    download_data = {}
    total_objects = 0
    
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2 and row[0].strip() and row[1].strip():
                folder = row[0].strip()
                uid = row[1].strip()
                
                # 构建相对路径
                relative_path = f"glbs/{folder}/{uid}.glb"
                download_data[uid] = relative_path
                total_objects += 1
    
    print(f"找到 {total_objects} 个对象需要下载")
    
    # 保存到JSON文件
    with open(output_json_file, 'w') as f:
        json.dump(download_data, f, indent=2)
    
    print(f"下载列表已保存到 {output_json_file}")
    return total_objects

def download_objects(json_file, batch_size=50):
    """批量下载对象"""
    print(f"开始批量下载对象，每批 {batch_size} 个...")
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    all_uids = list(data.keys())
    total_objects = len(all_uids)
    
    print(f"总共需要下载 {total_objects} 个对象")
    
    # 分批下载
    for i in range(0, total_objects, batch_size):
        batch_end = min(i + batch_size, total_objects)
        batch_uids = all_uids[i:batch_end]
        
        print(f"\n下载批次 {i//batch_size + 1}: 对象 {i+1}-{batch_end}")
        
        # 创建临时下载文件
        temp_file = f"temp_download_batch_{i//batch_size + 1}.json"
        temp_data = {uid: data[uid] for uid in batch_uids}
        
        with open(temp_file, 'w') as f:
            json.dump(temp_data, f)
        
        try:
            # 运行下载脚本
            cmd = [
                sys.executable, "download.py",
                "--obj_list", temp_file,
                "--begin_uid", "0",
                "--end_uid", str(len(batch_uids))
            ]
            
            print(f"执行下载命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)  # 2小时超时
            
            if result.returncode == 0:
                print(f"批次 {i//batch_size + 1} 下载完成!")
            else:
                print(f"批次 {i//batch_size + 1} 下载失败: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"批次 {i//batch_size + 1} 下载超时!")
        except Exception as e:
            print(f"批次 {i//batch_size + 1} 下载过程中出现错误: {e}")
        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        # 批次间暂停
        if batch_end < total_objects:
            print("等待5秒后继续下一批次...")
            time.sleep(5)
    
    print(f"\n所有批次下载完成!")

def check_existing_objects(csv_file):
    """检查已存在的对象"""
    print("检查已存在的对象...")
    
    source_base = "/projects/vig/Datasets/objaverse/hf-objaverse-v1/"
    existing_count = 0
    missing_count = 0
    
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2 and row[0].strip() and row[1].strip():
                folder = row[0].strip()
                uid = row[1].strip()
                
                # 构建源文件路径
                source_path = os.path.join(source_base, "glbs", folder, f"{uid}.glb")
                
                if os.path.exists(source_path):
                    existing_count += 1
                else:
                    missing_count += 1
    
    print(f"已存在的对象: {existing_count}")
    print(f"缺失的对象: {missing_count}")
    print(f"总计对象: {existing_count + missing_count}")
    
    return existing_count, missing_count

def main():
    """主函数"""
    csv_file = "test_obj.csv"
    json_file = "test_objects_download_list.json"
    
    # 检查CSV文件是否存在
    if not os.path.exists(csv_file):
        print(f"错误: 找不到文件 {csv_file}")
        return
    
    # 检查download.py是否存在
    if not os.path.exists("download.py"):
        print("错误: 找不到 download.py 文件")
        return
    
    print("开始处理test_obj.csv中的对象...")
    
    # 检查已存在的对象
    existing, missing = check_existing_objects(csv_file)
    
    if missing == 0:
        print("所有对象都已存在，无需下载!")
        return
    
    # 创建下载列表
    total_objects = create_download_list_from_csv(csv_file, json_file)
    
    # 询问用户是否继续
    response = input(f"\n发现 {missing} 个缺失对象，是否开始下载? (y/n): ")
    if response.lower() != 'y':
        print("下载已取消")
        return
    
    # 开始下载
    download_objects(json_file, batch_size=50)
    
    # 最终检查
    print("\n下载完成，进行最终检查...")
    existing_final, missing_final = check_existing_objects(csv_file)
    
    print(f"\n最终结果:")
    print(f"已存在的对象: {existing_final}")
    print(f"仍然缺失的对象: {missing_final}")
    print(f"下载成功率: {((existing_final - existing) / missing * 100):.1f}%")

if __name__ == "__main__":
    main()
