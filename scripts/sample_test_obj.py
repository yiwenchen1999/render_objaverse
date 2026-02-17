#!/usr/bin/env python3
"""从 filtered_uids.csv 中随机抽取 10000 条不与 test_obj.csv 重叠的样本，追加到 test_obj.csv。"""
import random

FILTERED_CSV = "filtered_uids.csv"
TEST_CSV = "test_obj.csv"
N_SAMPLE = 10000

def main():
    # 读取 test_obj.csv 中已有行（用于去重）
    with open(TEST_CSV, "r") as f:
        existing = {line.strip() for line in f if line.strip()}

    print(f"test_obj.csv 现有行数: {len(existing)}")

    # 读取 filtered_uids.csv，排除已有行
    with open(FILTERED_CSV, "r") as f:
        all_lines = [line.strip() for line in f if line.strip()]

    candidate = [line for line in all_lines if line not in existing]
    print(f"filtered_uids.csv 总行数: {len(all_lines)}")
    print(f"排除已有后候选数: {len(candidate)}")

    if len(candidate) < N_SAMPLE:
        raise SystemExit(f"候选数量 {len(candidate)} < 需要的 {N_SAMPLE}，无法抽样。")

    chosen = random.sample(candidate, N_SAMPLE)

    # 追加到 test_obj.csv
    with open(TEST_CSV, "a") as f:
        for line in chosen:
            f.write(line + "\n")

    print(f"已向 test_obj.csv 追加 {N_SAMPLE} 条新样本。")
    print(f"test_obj.csv 当前总行数: {len(existing) + N_SAMPLE}")

if __name__ == "__main__":
    main()
