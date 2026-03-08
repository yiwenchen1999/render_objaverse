#!/usr/bin/env python3
"""
Multi-worker dispatcher for render_3dscenes_dense_diff.py on Sony cluster.
Spawns multiple Blender processes per GPU for better utilization.

Usage:
  python SonyAIClusterUtil/distribute_render_3dscenes_diff_sony.py \
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

        scene_idx = item
        print(f"[GPU {gpu}] Rendering scene {scene_idx}", flush=True)

        # Build Blender command - calls render_3dscenes_dense_diff.py
        command = (
            f"CUDA_VISIBLE_DEVICES={gpu} "
            f"SDL_AUDIODRIVER=dummy "
            f"{blender_bin} -b -P {args.proj_root}/render_3dscenes_dense_diff.py -- "
            f"--group_start {scene_idx} --group_end {scene_idx + 1} "
            f"--num_views {args.num_views} "
            f"--num_test_views {args.num_test_views} "
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
            f"--glbs_root_path {args.glbs_root_path} "
            f"--env_map_dir_path {args.env_map_dir} "
            f"--white_env_map_dir_path {args.env_map_dir}"
        )

        if getattr(args, 'lq_list_path', None):
            command += f" --lq_list_path {args.lq_list_path}"
        if getattr(args, 'env_map_list_json', None):
            command += f" --env_map_list_json {args.env_map_list_json}"

        try:
            subprocess.run(command, shell=True, check=True)
            with count.get_lock():
                count.value += 1
        except subprocess.CalledProcessError as e:
            print(f"[GPU {gpu}] Failed to render scene {scene_idx}: {e}", flush=True)
        except Exception as e:
            print(f"[GPU {gpu}] Unexpected error for scene {scene_idx}: {e}", flush=True)

        queue.task_done()


def main():
    parser = argparse.ArgumentParser(description="Multi-worker dispatcher for 3D scene rendering (render_3dscenes_dense_diff, Sony cluster)")
    parser.add_argument("--workers_per_gpu", type=int, default=2, help="Number of workers per GPU")
    parser.add_argument("--num_gpus", type=int, default=1, help="Number of GPUs to use")
    parser.add_argument("--group_start", type=int, default=0, help="Start scene index")
    parser.add_argument("--group_end", type=int, default=50, help="End scene index")
    parser.add_argument("--output_dir", type=str, default="./output_scenes_diff")
    parser.add_argument("--model_lq_dir", type=str, default="/music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_models")
    parser.add_argument("--texture_dir", type=str, default="/music-shared-disk/group/ct/yiwen/data/objaverse/polyhaven_textures")
    parser.add_argument("--env_map_dir", type=str, default="/music-shared-disk/group/ct/yiwen/data/objaverse/hdris")
    parser.add_argument("--glb_list_path", type=str, default="test_obj_curated.csv")
    parser.add_argument("--glbs_root_path", type=str, default="/music-shared-disk/group/ct/yiwen/data/objaverse/objaverse/hf-objaverse-v1/glbs/")
    parser.add_argument("--lq_list_path", type=str, default=None, help="Path to LQ model list JSON (optional)")
    parser.add_argument("--env_map_list_json", type=str, default=None, help="Path to env map list JSON (optional)")
    parser.add_argument("--num_views", type=int, default=30, help="Number of training views")
    parser.add_argument("--num_test_views", type=int, default=50, help="Number of test views")
    parser.add_argument("--num_white_envs", type=int, default=1)
    parser.add_argument("--num_env_lights", type=int, default=5)
    parser.add_argument("--num_white_pls", type=int, default=0)
    parser.add_argument("--num_rgb_pls", type=int, default=0)
    parser.add_argument("--num_multi_pls", type=int, default=0)
    parser.add_argument("--num_area_lights", type=int, default=0)
    parser.add_argument("--num_combined_lights", type=int, default=0)
    parser.add_argument("--proj_root", type=str, default="/music-shared-disk/group/ct/yiwen/codes/render_objaverse")
    parser.add_argument("--blender_bin", type=str, default=None, help="Path to Blender binary")
    args = parser.parse_args()

    scene_indices = list(range(args.group_start, args.group_end))
    total = len(scene_indices)
    print(f"Distributing {total} scenes (render_3dscenes_dense_diff) across {args.num_gpus} GPUs with {args.workers_per_gpu} workers each")
    print(f"Project root: {args.proj_root}")
    print(f"GLBs root: {args.glbs_root_path}")

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
