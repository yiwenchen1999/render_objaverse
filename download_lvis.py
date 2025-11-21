#!/usr/bin/env python3
"""
从 filtered_uids_lvis.csv 下载 Objaverse 模型。

示例:
    python download_lvis.py \
        --csv_path ./filtered_uids_lvis.csv \
        --base_path /projects/vig/Datasets \
        --begin_uid 0 \
        --end_uid 100 \
        --download_processes 2
"""

import argparse
import csv
import os
import sys

import objaverse


def parse_args():
    parser = argparse.ArgumentParser(
        description="从 filtered_uids_lvis.csv 下载 Objaverse 模型"
    )
    parser.add_argument(
        "--csv_path",
        type=str,
        default="./filtered_uids_lvis.csv",
        help="CSV 文件路径（格式: folder,uid）"
    )
    parser.add_argument(
        "--base_path",
        type=str,
        default="/projects/vig/Datasets",
        help="Objaverse 数据集根目录（不含 objaverse 子目录）"
    )
    parser.add_argument(
        "--begin_uid",
        type=int,
        default=0,
        help="起始 UID 索引（从 0 开始）"
    )
    parser.add_argument(
        "--end_uid",
        type=int,
        default=100,
        help="结束 UID 索引（不包含）"
    )
    parser.add_argument(
        "--download_processes",
        type=int,
        default=2,
        help="下载进程数"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 设置 objaverse 路径
    objaverse.BASE_PATH = os.path.join(args.base_path, "objaverse")
    objaverse._VERSIONED_PATH = os.path.join(objaverse.BASE_PATH, "hf-objaverse-v1")

    print(f"Objaverse 版本: {objaverse.__version__}")
    print(f"Base path: {objaverse.BASE_PATH}")
    print(f"Versioned path: {objaverse._VERSIONED_PATH}")

    # 读取 CSV 文件
    if not os.path.exists(args.csv_path):
        print(f"错误: CSV 文件不存在: {args.csv_path}", file=sys.stderr)
        return 1

    index_uid_list = []
    with open(args.csv_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) == 2:
                folder, uid = row
                index_uid_list.append((folder.strip(), uid.strip()))

    print(f"成功加载 {len(index_uid_list)} 个条目")

    # 检查索引范围
    if args.begin_uid < 0 or args.begin_uid >= len(index_uid_list):
        print(f"错误: begin_uid ({args.begin_uid}) 超出范围 [0, {len(index_uid_list)})", file=sys.stderr)
        return 1

    if args.end_uid > len(index_uid_list):
        print(f"警告: end_uid ({args.end_uid}) 超出范围，将使用 {len(index_uid_list)}")
        args.end_uid = len(index_uid_list)

    if args.begin_uid >= args.end_uid:
        print(f"错误: begin_uid ({args.begin_uid}) >= end_uid ({args.end_uid})", file=sys.stderr)
        return 1

    # 提取要下载的 UID 列表
    download_uids = [uid for folder, uid in index_uid_list[args.begin_uid:args.end_uid]]

    print(f"准备下载 {len(download_uids)} 个模型 (索引 {args.begin_uid} 到 {args.end_uid})")
    print(f"下载进程数: {args.download_processes}")

    # 下载模型
    try:
        objects = objaverse.load_objects(
            uids=download_uids,
            download_processes=args.download_processes,
        )
        print(f"成功下载 {len(objects)} 个对象")
        print(f"下载的对象: {list(objects.keys())[:10]}..." if len(objects) > 10 else f"下载的对象: {list(objects.keys())}")
        return 0
    except Exception as e:
        print(f"下载过程中出错: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

