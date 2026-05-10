import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np


ANCHOR_C2W = np.array(
    [
        [0.0, 0.0, 1.0, 1.0],
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ],
    dtype=np.float64,
)


@dataclass
class RenderOptions:
    repo_dir: str
    output_subdir: str = "rerendered"
    resolution: int = 256
    fov_deg: float = 30.0
    device: str = "GPU"
    samples: int = 64
    max_scenes: int = -1
    dry_run: bool = False
    verbose: bool = False
    fail_fast: bool = False
    target_env_index: int = 1
    env_strength: float = 1.0


def _parse_blender_args() -> RenderOptions:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = argv[1:]

    parser = argparse.ArgumentParser(
        description="Batch rerender sf3d scenes with anchored camera remapping."
    )
    parser.add_argument("--repo-dir", required=True, type=str)
    parser.add_argument("--output-subdir", default="rerendered", type=str)
    parser.add_argument("--resolution", default=256, type=int)
    parser.add_argument("--fov-deg", default=30.0, type=float)
    parser.add_argument("--device", default="GPU", choices=["GPU", "CPU"])
    parser.add_argument("--samples", default=64, type=int)
    parser.add_argument("--max-scenes", default=-1, type=int)
    parser.add_argument("--target-env-index", default=1, choices=[1, 2], type=int)
    parser.add_argument("--env-strength", default=1.0, type=float)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--fail-fast", action="store_true")
    args = parser.parse_args(argv)
    return RenderOptions(**vars(args))


def _log(msg: str) -> None:
    print(msg, flush=True)


def _vlog(opts: RenderOptions, msg: str) -> None:
    if opts.verbose:
        _log(msg)


def _find_scene_dirs(repo_dir: Path) -> List[Path]:
    scenes: List[Path] = []
    for p in sorted(repo_dir.iterdir()):
        if not p.is_dir():
            continue
        if (p / "mesh_00.glb").exists() and (p / "mesh_01.glb").exists():
            scenes.append(p)
    return scenes


def _parse_iter_id(iter_name: str) -> int:
    m = re.fullmatch(r"iter_(\d+)", iter_name)
    if not m:
        return -1
    return int(m.group(1))


def _pick_latest_iter(scene_dir: Path) -> Path:
    iter_dirs = [p for p in scene_dir.iterdir() if p.is_dir() and _parse_iter_id(p.name) >= 0]
    if not iter_dirs:
        raise FileNotFoundError(f"No iter_* folder found in {scene_dir}")
    return max(iter_dirs, key=lambda p: _parse_iter_id(p.name))


def _required_paths(iter_dir: Path) -> List[Path]:
    req = [
        iter_dir / "camera_context_view_01.json",
        iter_dir / "camera_context_view_02.json",
    ]
    for i in range(1, 9):
        req.append(iter_dir / f"camera_target_view_{i:02d}.json")
    return req


def _resolve_env_pair(iter_dir: Path, view_idx: int) -> Tuple[Path, Path]:
    hdr_candidates = [
        iter_dir / "context_envhdr" / f"ldr_view_{view_idx:02d}.png",
        iter_dir / f"context_envhdr_view_{view_idx:02d}.png",
    ]
    ldr_candidates = [
        iter_dir / "context_envldr" / f"ldr_view_{view_idx:02d}.png",
        iter_dir / f"context_envldr_view_{view_idx:02d}.png",
    ]

    hdr_path = next((p for p in hdr_candidates if p.exists()), None)
    ldr_path = next((p for p in ldr_candidates if p.exists()), None)
    if hdr_path is None or ldr_path is None:
        raise FileNotFoundError(
            f"Cannot find env pair for view_{view_idx:02d} in {iter_dir}. "
            f"Tried hdr={hdr_candidates}, ldr={ldr_candidates}"
        )
    return hdr_path, ldr_path


def _check_required_files(iter_dir: Path) -> None:
    missing = [str(p) for p in _required_paths(iter_dir) if not p.exists()]
    try:
        _resolve_env_pair(iter_dir, 1)
        _resolve_env_pair(iter_dir, 2)
    except FileNotFoundError as e:
        missing.append(str(e))
    if missing:
        msg = "Missing required files:\n  - " + "\n  - ".join(missing)
        raise FileNotFoundError(msg)


def _load_pose(json_path: Path) -> np.ndarray:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    c2w = np.array(data["c2w"], dtype=np.float64)
    if c2w.shape != (4, 4):
        raise ValueError(f"Invalid c2w shape in {json_path}: {c2w.shape}")
    return c2w


def _pose_json_template(c2w: np.ndarray, role: str, view_index: int, fov_deg: float) -> Dict:
    return {
        "role": role,
        "view_index": view_index,
        "c2w": c2w.tolist(),
        "fov_deg": fov_deg,
    }


def _reconstruct_hdr_from_pair(hdr_png_path: Path, ldr_png_path: Path) -> np.ndarray:
    import imageio.v3 as imageio  # pyright: ignore[reportMissingImports]

    hdr_png = imageio.imread(hdr_png_path)[..., :3].astype(np.float64) / 255.0
    ldr_png = imageio.imread(ldr_png_path)[..., :3].astype(np.float64) / 255.0

    ldr_linear = np.power(ldr_png, 2.2)
    hdr_norm = hdr_png
    non_sat = (ldr_linear > 0.01) & (ldr_linear < 0.95) & (hdr_norm > 0.01)
    if np.any(non_sat):
        max_log = np.median(np.log1p(10.0 * ldr_linear[non_sat]) / hdr_norm[non_sat])
    else:
        max_log = np.log1p(10.0)
    raw_hdr = np.expm1(hdr_norm * max_log) / 10.0
    return raw_hdr.astype(np.float32)


def _save_hdr_with_fallback(hdr_img: np.ndarray, out_dir: Path, stem: str) -> Path:
    import imageio.v3 as imageio  # pyright: ignore[reportMissingImports]

    out_dir.mkdir(parents=True, exist_ok=True)
    exr_path = out_dir / f"{stem}.exr"
    try:
        imageio.imwrite(exr_path, hdr_img)
        return exr_path
    except Exception:
        hdr_path = out_dir / f"{stem}.hdr"
        imageio.imwrite(hdr_path, hdr_img)
        return hdr_path


def _compute_remapped_poses(iter_dir: Path) -> Tuple[np.ndarray, np.ndarray, List[np.ndarray], Dict]:
    ctx1 = _load_pose(iter_dir / "camera_context_view_01.json")
    ctx2 = _load_pose(iter_dir / "camera_context_view_02.json")
    inv_ctx1 = np.linalg.inv(ctx1)

    ctx1_bl = ANCHOR_C2W.copy()
    ctx2_bl = ANCHOR_C2W @ (inv_ctx1 @ ctx2)
    targets_bl: List[np.ndarray] = []
    rel_targets: List[np.ndarray] = []

    for i in range(1, 9):
        t = _load_pose(iter_dir / f"camera_target_view_{i:02d}.json")
        rel = inv_ctx1 @ t
        rel_targets.append(rel)
        targets_bl.append(ANCHOR_C2W @ rel)

    metadata = {
        "anchor_c2w": ANCHOR_C2W.tolist(),
        "context_view_01_json": ctx1.tolist(),
        "context_view_02_json": ctx2.tolist(),
        "context_view_02_relative_to_context_view_01": (inv_ctx1 @ ctx2).tolist(),
        "target_relative_to_context_view_01": [x.tolist() for x in rel_targets],
    }
    return ctx1_bl, ctx2_bl, targets_bl, metadata


def _configure_blender(opts: RenderOptions) -> None:
    import bpy  # pyright: ignore[reportMissingImports]

    scene = bpy.context.scene
    scene.render.resolution_x = opts.resolution
    scene.render.resolution_y = opts.resolution
    scene.render.engine = "CYCLES"
    scene.cycles.samples = opts.samples

    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True

    scene.cycles.device = opts.device
    if opts.device == "GPU":
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.get_devices()
        for device_type in ["OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"]:
            try:
                prefs.compute_device_type = device_type
                break
            except Exception:
                continue


def _render_single_view(c2w: np.ndarray, fov_deg: float, out_path: Path) -> None:
    import bpy  # pyright: ignore[reportMissingImports]
    from bpy_helper.camera import create_camera

    cam = create_camera(c2w, fov_deg)
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = str(out_path)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)


def _process_scene(scene_dir: Path, opts: RenderOptions) -> None:
    from bpy_helper.light import set_env_light
    from bpy_helper.scene import import_3d_model, reset_scene
    from bpy_helper.utils import stdout_redirected

    iter_dir = _pick_latest_iter(scene_dir)
    _check_required_files(iter_dir)

    out_dir = scene_dir / opts.output_subdir
    env_tmp_dir = out_dir / "_tmp_env"
    out_dir.mkdir(parents=True, exist_ok=True)

    ctx1_bl, ctx2_bl, targets_bl, pose_meta = _compute_remapped_poses(iter_dir)

    hdr01_path, ldr01_path = _resolve_env_pair(iter_dir, 1)
    hdr02_path, ldr02_path = _resolve_env_pair(iter_dir, 2)
    env01 = _reconstruct_hdr_from_pair(
        hdr01_path,
        ldr01_path,
    )
    env02 = _reconstruct_hdr_from_pair(
        hdr02_path,
        ldr02_path,
    )
    env01_path = _save_hdr_with_fallback(env01, env_tmp_dir, "context_env_01")
    env02_path = _save_hdr_with_fallback(env02, env_tmp_dir, "context_env_02")
    target_env_path = env01_path if opts.target_env_index == 1 else env02_path

    reset_scene()
    with stdout_redirected():
        import_3d_model(str(scene_dir / "mesh_00.glb"))
        import_3d_model(str(scene_dir / "mesh_01.glb"))

    _configure_blender(opts)

    set_env_light(str(env01_path), strength=opts.env_strength)
    _render_single_view(ctx1_bl, opts.fov_deg, out_dir / "context_view_01.png")

    set_env_light(str(env02_path), strength=opts.env_strength)
    _render_single_view(ctx2_bl, opts.fov_deg, out_dir / "context_view_02.png")

    set_env_light(str(target_env_path), strength=opts.env_strength)
    for i, t_bl in enumerate(targets_bl, start=1):
        _render_single_view(t_bl, opts.fov_deg, out_dir / f"target_view_{i:02d}.png")

    with open(out_dir / "camera_context_view_01.json", "w", encoding="utf-8") as f:
        json.dump(_pose_json_template(ctx1_bl, "context", 1, opts.fov_deg), f, indent=2)
    with open(out_dir / "camera_context_view_02.json", "w", encoding="utf-8") as f:
        json.dump(_pose_json_template(ctx2_bl, "context", 2, opts.fov_deg), f, indent=2)
    for i, t_bl in enumerate(targets_bl, start=1):
        with open(out_dir / f"camera_target_view_{i:02d}.json", "w", encoding="utf-8") as f:
            json.dump(_pose_json_template(t_bl, "target", i, opts.fov_deg), f, indent=2)

    with open(out_dir / "rerender_meta.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "scene_name": scene_dir.name,
                "source_iter": iter_dir.name,
                "mesh_paths": ["mesh_00.glb", "mesh_01.glb"],
                "target_env_index": opts.target_env_index,
                "env_strength": opts.env_strength,
                "resolution": opts.resolution,
                "fov_deg": opts.fov_deg,
                "pose_mapping": pose_meta,
            },
            f,
            indent=2,
        )


def main() -> None:
    opts = _parse_blender_args()
    repo_dir = Path(opts.repo_dir).resolve()
    if not repo_dir.exists():
        raise FileNotFoundError(f"repo dir does not exist: {repo_dir}")

    scene_dirs = _find_scene_dirs(repo_dir)
    if opts.max_scenes > 0:
        scene_dirs = scene_dirs[: opts.max_scenes]

    if not scene_dirs:
        _log(f"No scene folders found under {repo_dir}")
        return

    _log(f"[rerender] repo_dir={repo_dir}")
    _log(f"[rerender] scenes={len(scene_dirs)} output_subdir={opts.output_subdir}")

    for idx, scene_dir in enumerate(scene_dirs, start=1):
        try:
            iter_dir = _pick_latest_iter(scene_dir)
            _check_required_files(iter_dir)
            _vlog(
                opts,
                f"[{idx}/{len(scene_dirs)}] {scene_dir.name} iter={iter_dir.name} "
                f"target_env_index={opts.target_env_index}",
            )
            if opts.dry_run:
                continue
            _process_scene(scene_dir, opts)
            _log(f"[done] {scene_dir.name}")
        except Exception as exc:
            _log(f"[error] {scene_dir.name}: {exc}")
            if opts.fail_fast:
                raise


if __name__ == "__main__":
    main()
