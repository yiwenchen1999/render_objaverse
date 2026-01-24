#!/usr/bin/env python3
"""
从 filtered_uids.csv 中随机选择 2000 个项目添加到 test_obj.csv
确保不与 test_obj.csv 中已有的项目重叠
"""
import csv
import random
import os
from typing import Set, List, Tuple

def load_csv_entries(csv_path: str) -> Set[Tuple[str, str]]:
    """
    加载 CSV 文件中的所有条目，返回 (index, uid) 的集合
    """
    entries = set()
    if not os.path.exists(csv_path):
        print(f"警告: 文件 {csv_path} 不存在")
        return entries
    
    with open(csv_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                index = row[0].strip()
                uid = row[1].strip()
                if index and uid:  # 确保不是空行
                    entries.add((index, uid))
    
    return entries

def save_csv_entries(csv_path: str, entries: List[Tuple[str, str]], append: bool = False):
    """
    将条目保存到 CSV 文件
    """
    mode = 'a' if append else 'w'
    with open(csv_path, mode, encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        for index, uid in entries:
            writer.writerow([index, uid])

def main():
    test_obj_path = 'test_obj.csv'
    filtered_uids_path = 'filtered_uids.csv'
    num_to_select = 2000
    
    print("=" * 60)
    print("从 filtered_uids.csv 随机选择项目添加到 test_obj.csv")
    print("=" * 60)
    
    # 1. 加载 test_obj.csv 中已有的条目
    print(f"\n1. 加载 {test_obj_path} 中已有的条目...")
    existing_entries = load_csv_entries(test_obj_path)
    print(f"   已找到 {len(existing_entries)} 个现有条目")
    
    # 2. 加载 filtered_uids.csv 中的所有条目
    print(f"\n2. 加载 {filtered_uids_path} 中的所有条目...")
    all_filtered_entries = load_csv_entries(filtered_uids_path)
    print(f"   共找到 {len(all_filtered_entries)} 个条目")
    
    # 3. 找出不在 test_obj.csv 中的条目
    print(f"\n3. 找出不在 {test_obj_path} 中的条目...")
    available_entries = all_filtered_entries - existing_entries
    print(f"   可用条目数: {len(available_entries)}")
    
    if len(available_entries) < num_to_select:
        print(f"\n警告: 可用条目数 ({len(available_entries)}) 少于请求的数量 ({num_to_select})")
        print(f"将选择所有 {len(available_entries)} 个可用条目")
        num_to_select = len(available_entries)
    
    # 4. 随机选择指定数量的条目
    print(f"\n4. 随机选择 {num_to_select} 个条目...")
    available_list = list(available_entries)
    random.shuffle(available_list)
    selected_entries = available_list[:num_to_select]
    
    print(f"   已选择 {len(selected_entries)} 个条目")
    
    # 5. 追加到 test_obj.csv
    print(f"\n5. 将选中的条目追加到 {test_obj_path}...")
    save_csv_entries(test_obj_path, selected_entries, append=True)
    print(f"   完成！已添加 {len(selected_entries)} 个新条目")
    
    # 6. 验证结果
    print(f"\n6. 验证结果...")
    updated_entries = load_csv_entries(test_obj_path)
    print(f"   {test_obj_path} 现在包含 {len(updated_entries)} 个条目")
    print(f"   (原有: {len(existing_entries)}, 新增: {len(selected_entries)})")
    
    # 检查是否有重叠
    overlap = existing_entries & set(selected_entries)
    if overlap:
        print(f"\n警告: 发现 {len(overlap)} 个重叠条目！")
        for idx, uid in list(overlap)[:10]:  # 只显示前10个
            print(f"   {idx},{uid}")
        if len(overlap) > 10:
            print(f"   ... 还有 {len(overlap) - 10} 个重叠条目")
    else:
        print(f"\n✓ 验证通过: 没有发现重叠条目")
    
    print("\n" + "=" * 60)
    print("任务完成！")
    print("=" * 60)

if __name__ == '__main__':
    # 设置随机种子以便结果可复现（可选）
    # random.seed(42)
    main()

