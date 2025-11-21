#!/usr/bin/env python3
"""
根据 LVIS 注释过滤 test_obj.csv 中的对象，只保留带有 LVIS 标签的 UID。

示例:

    python filter_test_obj_lvis.py \
        --base_path /projects/vig/Datasets \
        --input test_obj.csv \
        --output test_obj_LVIS.csv
"""

from __future__ import annotations

import argparse
import csv
import os
import sys

import objaverse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="只保留 LVIS 注释中存在的 Objaverse UID"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=os.path.join(os.getcwd(), "test_obj.csv"),
        help="包含 UUID 的原始 CSV (folder,uid)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=os.path.join(os.getcwd(), "test_obj_LVIS.csv"),
        help="输出过滤后的 CSV",
    )
    parser.add_argument(
        "--base_path",
        type=str,
        default=os.getcwd(),
        help="Objaverse 数据集根目录（不含 objaverse 子目录），默认当前工作目录",
    )
    parser.add_argument(
        "--versioned_path",
        type=str,
        default="",
        help="可选的 objaverse 版本目录（将覆盖默认的 hf-objaverse-v1）",
    )
    return parser.parse_args()


def prepare_objaverse_paths(base_path: str, versioned_path: str) -> None:
    objaverse.BASE_PATH = os.path.join(base_path, "objaverse")
    if versioned_path:
        objaverse._VERSIONED_PATH = versioned_path
    else:
        objaverse._VERSIONED_PATH = os.path.join(objaverse.BASE_PATH, "hf-objaverse-v1")


def load_lvis_uid_set() -> set[str]:
    annotations = objaverse.load_lvis_annotations()
    uid_set: set[str] = set()
    for uid_list in annotations.values():
        uid_set.update(uid_list)
    return uid_set


def filter_csv(input_csv: str, lvise_uids: set[str]) -> list[tuple[str, str]]:
    kept: list[tuple[str, str]] = []
    with open(input_csv, newline="") as fp:
        reader = csv.reader(fp)
        for row in reader:
            if len(row) < 2:
                continue
            folder, uid = row[0].strip(), row[1].strip()
            if not folder or not uid:
                continue
            if uid in lvise_uids:
                kept.append((folder, uid))
    return kept


def dump_csv(output_csv: str, rows: list[tuple[str, str]]) -> None:
    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
    with open(output_csv, "w", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerows(rows)


def main() -> int:
    args = parse_args()

    prepare_objaverse_paths(args.base_path, args.versioned_path)

    try:
        lvis_uid_set = load_lvis_uid_set()
    except Exception as exc:  # pragma: no cover - runtime guard
        print(f"无法加载 LVIS 注释：{exc}", file=sys.stderr)
        return 1

    filtered = filter_csv(args.input, lvis_uid_set)
    dump_csv(args.output, filtered)

    print(f"读取 {args.input} → {len(filtered)} 条 LVIS UID")
    print(f"输出结果到 {args.output} (原始记录在 {len(filtered)} 条)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

