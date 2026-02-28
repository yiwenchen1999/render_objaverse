#!/usr/bin/env python3
"""
Multi-worker dispatcher for render_3dscenes_dense.py on Explorer cluster.
Spawns multiple Blender processes per GPU for better utilization.

Usage:
  python scripts/distribute_render_3dscenes.py \
    --num_gpus 1 --workers_per_gpu 4 \
    --group_start 0 --group_end 50
"""

import argparse
import json
import multiprocessing
import os
import signal
import subprocess
import sys


def worker(
    queue: multiprocessing.JoinableQueue,
    count: multiprocessing.Value,
    gpu: int,
    args: argparse.Namespace,
) -> None:
    """Worker process: render scenes from queue on specified GPU."""
    
    while True:
        item = queue.get()
        if item is None:
            break

        scene_idx = item
        print(f"[GPU {gpu}] Rendering scene {scene_idx}")

        # Build command
        command = (
            f"CUDA_VISIBLE_DEVICES={gpu} "
            f"python {args.proj_root}/render_3dscenes_dense.py "
            f"--group_start {scene_idx} --group_end {scene_idx + 1} "
            f"--num_white_envs {args.num_white_envs} "
            f"--num_env_lights {args.num_env_lights} "
            f"--num_white_pls {args.num_white_pls} "
            f"--num_rgb_pls {args.num_rgb_pls} "
            f"--num_multi_pls {args.num_multi_pls} "
            f"--num_area_lights {args.num_area_lights} "
            f"--num_combined_lights {args.num_combined_lights} "
            f"--model_lq_dir {args.model_lq_dir} "
            f"--output_dir {args.output_dir} "
            f"--texture_dir {args.texture_dir} "
            f"--glb_list_path {args.glb_list_path} "
            f"--glbs_root_path {args.glbs_root_path}"

        )

        try:
            subprocess.run(command, shell=True, check=True)
            with count.get_lock():
                count.value += 1
        except subprocess.CalledProcessError as e:
            print(f"[GPU {gpu}] Failed to render scene {scene_idx}: {e}")
        except Exception as e:
            print(f"[GPU {gpu}] Unexpected error for scene {scene_idx}: {e}")

        queue.task_done()


def main():
    parser = argparse.ArgumentParser(description="Multi-worker dispatcher for 3D scene rendering")
    parser.add_argument("--workers_per_gpu", type=int, default=2, help="Number of workers per GPU")
    parser.add_argument("--num_gpus", type=int, default=1, help="Number of GPUs to use")
    parser.add_argument("--group_start", type=int, default=0, help="Start scene index")
    parser.add_argument("--group_end", type=int, default=50, help="End scene index")
    parser.add_argument("--output_dir", type=str, default="./output_scenes_dense")
    parser.add_argument("--model_lq_dir", type=str, default="/projects/vig/Datasets/Polyhaven/polyhaven_models")
    parser.add_argument("--texture_dir", type=str, default="/projects/vig/Datasets/Polyhaven/polyhaven_textures")
    parser.add_argument("--glb_list_path", type=str, default="test_obj_curated.csv")
    parser.add_argument("--glbs_root_path", type=str, default="/projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/")
    parser.add_argument("--num_white_envs", type=int, default=1)
    parser.add_argument("--num_env_lights", type=int, default=3)
    parser.add_argument("--num_white_pls", type=int, default=0)
    parser.add_argument("--num_rgb_pls", type=int, default=0)
    parser.add_argument("--num_multi_pls", type=int, default=0)
    parser.add_argument("--num_area_lights", type=int, default=0)
    parser.add_argument("--num_combined_lights", type=int, default=0)
    parser.add_argument("--proj_root", type=str, default="/projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse")
    args = parser.parse_args()

    scene_indices = list(range(args.group_start, args.group_end))
    total = len(scene_indices)
    print(f"Distributing {total} scenes across {args.num_gpus} GPUs with {args.workers_per_gpu} workers each")

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
        # Enqueue all scenes
        for scene_idx in scene_indices:
            queue.put(scene_idx)

        # Wait for completion
        queue.join()

        # Stop workers
        for _ in range(args.num_gpus * args.workers_per_gpu):
            queue.put(None)

        print(f"All done! Rendered {count.value}/{total} scenes.")

    except KeyboardInterrupt:
        print("Received interrupt. Terminating workers.")
        for p in processes:
            os.kill(p.pid, signal.SIGKILL)


if __name__ == "__main__":
    main()
