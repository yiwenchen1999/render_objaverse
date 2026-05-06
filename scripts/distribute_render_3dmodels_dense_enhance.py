#!/usr/bin/env python3
"""
Multi-worker dispatcher for render_3dmodels_dense_enhance.py on Explorer cluster.
Spawns multiple Blender processes per GPU for better utilization.

Usage:
  python scripts/distribute_render_3dmodels_dense_enhance.py \
    --num_gpus 1 --workers_per_gpu 4 \
    --group_start 0 --group_end 50
"""

import argparse
import multiprocessing
import os
import random
import signal
import subprocess


def sample_light_config(model_idx: int, args: argparse.Namespace) -> dict:
    """Sample per-model lighting counts under fixed constraints."""
    total_lights = 6
    seed = model_idx if args.lighting_seed is None else args.lighting_seed + model_idx
    rng = random.Random(seed)

    use_combined = args.enable_combined and (rng.random() < args.combined_probability)

    if use_combined:
        # Combined lighting is a progressive 4-stage setup.
        cfg = {
            "num_combined_lights": 4,
            "num_white_envs": 1,
            "num_env_lights": 1,
            "num_white_pls": 0,
            "num_rgb_pls": 0,
            "num_multi_pls": 0,
            "num_area_lights": 0,
        }
    else:
        env_total = rng.randint(2, total_lights)  # enforce num_white_envs + num_env_lights > 1
        num_white_envs = rng.randint(1, env_total - 1)
        num_env_lights = env_total - num_white_envs

        remaining = total_lights - env_total
        point_and_area_keys = ["num_white_pls", "num_rgb_pls", "num_multi_pls", "num_area_lights"]
        extras = {key: 0 for key in point_and_area_keys}
        for _ in range(remaining):
            extras[rng.choice(point_and_area_keys)] += 1

        cfg = {
            "num_combined_lights": 0,
            "num_white_envs": num_white_envs,
            "num_env_lights": num_env_lights,
            **extras,
        }

    total = (
        cfg["num_combined_lights"]
        + cfg["num_white_envs"]
        + cfg["num_env_lights"]
        + cfg["num_white_pls"]
        + cfg["num_rgb_pls"]
        + cfg["num_multi_pls"]
        + cfg["num_area_lights"]
    )
    assert cfg["num_combined_lights"] in (0, 4)
    assert total == total_lights
    assert (cfg["num_white_envs"] + cfg["num_env_lights"]) > 1
    return cfg


def worker(
    queue: multiprocessing.JoinableQueue,
    count: multiprocessing.Value,
    gpu: int,
    args: argparse.Namespace,
) -> None:
    """Worker process: render models from queue on specified GPU."""

    while True:
        item = queue.get()
        if item is None:
            break

        model_idx = item
        if args.dynamic_lighting_counts:
            light_cfg = sample_light_config(model_idx, args)
        else:
            light_cfg = {
                "num_white_envs": args.num_white_envs,
                "num_env_lights": args.num_env_lights,
                "num_white_pls": args.num_white_pls,
                "num_rgb_pls": args.num_rgb_pls,
                "num_multi_pls": args.num_multi_pls,
                "num_area_lights": args.num_area_lights,
                "num_combined_lights": args.num_combined_lights,
            }

        print(f"[GPU {gpu}] Rendering model {model_idx} with lights: {light_cfg}", flush=True)

        command = (
            f"CUDA_VISIBLE_DEVICES={gpu} "
            f"python {args.proj_root}/render_3dmodels_dense_enhance.py "
            f"--group_start {model_idx} --group_end {model_idx + 1} "
            f"--num_views {args.num_views} "
            f"--num_test_views {args.num_test_views} "
            f"--num_white_envs {light_cfg['num_white_envs']} "
            f"--num_env_lights {light_cfg['num_env_lights']} "
            f"--num_white_pls {light_cfg['num_white_pls']} "
            f"--num_rgb_pls {light_cfg['num_rgb_pls']} "
            f"--num_multi_pls {light_cfg['num_multi_pls']} "
            f"--num_area_lights {light_cfg['num_area_lights']} "
            f"--num_combined_lights {light_cfg['num_combined_lights']} "
            f"--rendered_dir_name {args.rendered_dir_name} "
            f"--csv_path {args.csv_path}"
        )

        try:
            subprocess.run(command, shell=True, check=True)
            with count.get_lock():
                count.value += 1
        except subprocess.CalledProcessError as e:
            print(f"[GPU {gpu}] Failed to render model {model_idx}: {e}", flush=True)
        except Exception as e:
            print(f"[GPU {gpu}] Unexpected error for model {model_idx}: {e}", flush=True)

        queue.task_done()


def main():
    parser = argparse.ArgumentParser(
        description="Multi-worker dispatcher for render_3dmodels_dense_enhance.py"
    )
    parser.add_argument("--workers_per_gpu", type=int, default=2, help="Number of workers per GPU")
    parser.add_argument("--num_gpus", type=int, default=1, help="Number of GPUs to use")
    parser.add_argument("--group_start", type=int, default=0, help="Start model index")
    parser.add_argument("--group_end", type=int, default=50, help="End model index")
    parser.add_argument("--num_views", type=int, default=30, help="Number of training views")
    parser.add_argument("--num_test_views", type=int, default=50, help="Number of test views")
    parser.add_argument("--num_white_envs", type=int, default=1)
    parser.add_argument("--num_env_lights", type=int, default=0)
    parser.add_argument("--num_white_pls", type=int, default=3)
    parser.add_argument("--num_rgb_pls", type=int, default=1)
    parser.add_argument("--num_multi_pls", type=int, default=0)
    parser.add_argument("--num_area_lights", type=int, default=0)
    parser.add_argument("--num_combined_lights", type=int, default=0)
    parser.add_argument("--dynamic_lighting_counts", action="store_true")
    parser.add_argument("--enable_combined", action="store_true")
    parser.add_argument("--combined_probability", type=float, default=0.5)
    parser.add_argument("--lighting_seed", type=int, default=0)
    parser.add_argument("--rendered_dir_name", type=str, default="rendered_dense_enhance")
    parser.add_argument("--csv_path", type=str, default="test_obj.csv")
    parser.add_argument(
        "--proj_root",
        type=str,
        default="/projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse",
    )
    args = parser.parse_args()

    model_indices = list(range(args.group_start, args.group_end))
    total = len(model_indices)
    print(
        f"Distributing {total} models across {args.num_gpus} GPUs "
        f"with {args.workers_per_gpu} workers each"
    )

    queue = multiprocessing.JoinableQueue()
    count = multiprocessing.Value("i", 0)
    processes = []

    for gpu_i in range(args.num_gpus):
        for _worker_i in range(args.workers_per_gpu):
            process = multiprocessing.Process(target=worker, args=(queue, count, gpu_i, args))
            process.daemon = True
            process.start()
            processes.append(process)

    try:
        for model_idx in model_indices:
            queue.put(model_idx)

        queue.join()

        for _ in range(args.num_gpus * args.workers_per_gpu):
            queue.put(None)

        print(f"All done! Rendered {count.value}/{total} models.")

    except KeyboardInterrupt:
        print("Received interrupt. Terminating workers.")
        for p in processes:
            os.kill(p.pid, signal.SIGKILL)


if __name__ == "__main__":
    main()
