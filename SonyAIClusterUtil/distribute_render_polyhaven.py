#!/usr/bin/env python3
"""
Multi-worker dispatcher for render_3dmodels_dense_polyhaven.py.
Spawns multiple Blender processes per GPU for better utilization.

Usage:
  python SonyAIClusterUtil/distribute_render_polyhaven.py \
    --num_gpus 1 --workers_per_gpu 4 \
    --model_list_path assets/object_ids/polyhaven_models_train.json \
    --group_start 0 --group_end 60
"""

import json
import multiprocessing
import os
import signal
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional

import tyro


@dataclass
class Args:
    workers_per_gpu: int = 2
    """Number of Blender workers per GPU (2-4 recommended)"""

    num_gpus: int = 1
    """Number of GPUs to use"""

    model_list_path: str = "assets/object_ids/polyhaven_models_train.json"
    """Path to Polyhaven model list JSON"""

    group_start: int = 0
    """Start index in model list"""

    group_end: int = 10
    """End index in model list (exclusive)"""

    output_dir: str = "/music-shared-disk/group/ct/yiwen/data/objaverse/rendered_dense_polyhaven"
    """Output directory"""

    model_lq_dir: str = "/music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_models"
    """Path to Polyhaven models"""

    env_map_dir: str = "/music-shared-disk/group/ct/yiwen/data/objaverse/hdris"
    """Path to HDRI environment maps"""

    num_views: int = 30
    """Number of random views per model"""

    num_test_views: int = 100
    """Number of trajectory views per model"""

    cycles_tile_size: int = 512
    """Cycles tile size (max 512 for 512x512 renders)"""

    blender_bin: Optional[str] = None
    """Path to Blender binary (auto-detect if None)"""

    proj_root: str = "/music-shared-disk/group/ct/yiwen/codes/render_objaverse"
    """Project root directory"""


def worker(
    queue: multiprocessing.JoinableQueue,
    count: multiprocessing.Value,
    gpu: int,
    args: Args,
) -> None:
    """Worker process: render models from queue on specified GPU."""
    blender_bin = args.blender_bin
    if not blender_bin:
        # Auto-detect Blender
        blender_bin = os.path.join(args.proj_root, "neuralGaufferRendering/blender-3.2.2-linux-x64/blender")
        if not os.path.exists(blender_bin):
            blender_bin = os.path.join(args.proj_root, "neuralGaufferRendering/blender-4.2-linux-x64/blender")

    while True:
        item = queue.get()
        if item is None:
            break

        model_id = item
        # Check if already rendered
        res_dir = os.path.join(args.output_dir, model_id)
        if os.path.exists(os.path.join(res_dir, "done.txt")):
            print(f"[GPU {gpu}] Skipping {model_id} (already done)")
            queue.task_done()
            continue

        print(f"[GPU {gpu}] Rendering {model_id}")

        # Build Blender command
        command = (
            f"CUDA_VISIBLE_DEVICES={gpu} "
            f"SDL_AUDIODRIVER=dummy "
            f"{blender_bin} -b -P {args.proj_root}/render_3dmodels_dense_polyhaven.py -- "
            f"--single_model_id {model_id} "
            f"--output_dir {args.output_dir} "
            f"--model_lq_dir {args.model_lq_dir} "
            f"--env_map_dir_path {args.env_map_dir} "
            f"--white_env_map_dir_path {args.env_map_dir} "
            f"--model_list_path {args.proj_root}/{args.model_list_path} "
            f"--num_views {args.num_views} "
            f"--num_test_views {args.num_test_views} "
            f"--rendered_dir_name {args.output_dir} "
            f"--cycles_tile_size {args.cycles_tile_size} "
            f"--num_white_pls 3 --num_rgb_pls 1 --num_multi_pls 0 "
            f"--num_env_lights 4 --num_white_envs 1 --num_area_lights 0"
        )

        try:
            subprocess.run(command, shell=True, check=True)
            with count.get_lock():
                count.value += 1
        except subprocess.CalledProcessError as e:
            print(f"[GPU {gpu}] Failed to render {model_id}: {e}")
        except Exception as e:
            print(f"[GPU {gpu}] Unexpected error for {model_id}: {e}")

        queue.task_done()


def main():
    args = tyro.cli(Args)

    # Load model list
    with open(os.path.join(args.proj_root, args.model_list_path), "r") as f:
        model_list = json.load(f)

    # Slice model list by group_start/group_end
    model_ids = list(model_list.keys())[args.group_start : args.group_end]
    total = len(model_ids)
    print(f"Distributing {total} models across {args.num_gpus} GPUs with {args.workers_per_gpu} workers each")

    queue = multiprocessing.JoinableQueue()
    count = multiprocessing.Value("i", 0)
    processes = []

    # Start workers
    for gpu_i in range(args.num_gpus):
        for worker_i in range(args.workers_per_gpu):
            process = multiprocessing.Process(target=worker, args=(queue, count, gpu_i, args))
            process.daemon = True
            process.start()
            processes.append(process)

    try:
        # Enqueue all models
        for model_id in model_ids:
            queue.put(model_id)

        # Wait for completion
        queue.join()

        # Stop workers
        for _ in range(args.num_gpus * args.workers_per_gpu):
            queue.put(None)

        print(f"All done! Rendered {count.value}/{total} models.")

    except KeyboardInterrupt:
        print("Received interrupt. Terminating workers.")
        for p in processes:
            os.kill(p.pid, signal.SIGKILL)


if __name__ == "__main__":
    main()
