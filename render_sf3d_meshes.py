"""Render SF3D-generated meshes per scene with the matching context envmap.

Each scene directory under ``--data_root`` is expected to contain two SF3D
mesh predictions (``mesh_00.glb``, ``mesh_01.glb``) and an iteration subdir
(default ``iter_00000297``) holding the paired HDR/LDR encoded envmap pngs
(``context_envhdr_view_{01,02}.png``, ``context_envldr_view_{01,02}.(jpg|png)``).

For each mesh we:
    1. Reconstruct the HDR envmap from the (hdr_png, ldr_png) pair (mirroring
       ``dataset_polyhaven.reconstruct_hdr_from_pngs``) and stage it as a
       temporary ``.exr`` so Blender can load it; the temp file is removed
       once the render is done.
    2. Load the glb and (by default) normalize it via
       ``bpy_helper.scene.normalize_scene(use_bounding_sphere=True, target_scale=0.5)``,
       i.e. centered at origin with bounding sphere radius 0.5. Disable with
       ``--normalize False``.
    3. Place a Cycles camera at ``(0, -1, 0)`` looking at the origin with up=z.
    4. Render at the requested resolution and write back to the scene's iter
       subdir as ``rerender_view_{00,01}.png`` (always overwrites).
"""

import glob
import os
import sys
import tempfile
import traceback
from dataclasses import dataclass
from typing import Optional

# Ensure project root is on path so bpy_helper is found when run via Blender -b -P
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

import imageio
import imageio.v3 as iio
import numpy as np
import simple_parsing


@dataclass
class Options:
    """SF3D mesh rendering options."""

    data_root: str = "asset_samples/meshes_sf3d"
    iter_subdir: str = "iter_00000297"
    resolution: int = 512
    fov_deg: float = 30.0
    cycles_samples: int = 128
    env_rotation_z: float = 0.0
    env_strength: float = 1.0
    scene_filter: Optional[str] = None
    output_prefix: str = "rerender_view"
    normalize: bool = True  # bounding-sphere normalize (like render_3dmodels_dense_addLights.py)
    normalize_target_scale: float = 0.5  # bounding sphere radius after normalization
    normalize_use_bounding_sphere: bool = True


# --------------------------------------------------------------------------- #
# HDR reconstruction                                                          #
# --------------------------------------------------------------------------- #


def reconstruct_hdr_from_pair(hdr_png_path: str, ldr_path: str) -> np.ndarray:
    """Recover the linear HDR envmap from a (hdr_png, ldr_png/jpg) pair.

    Mirrors ``dataset_polyhaven.reconstruct_hdr_from_pngs``:
        ldr  = uint8( clip(raw, 0, 1) ** (1/2.2) * 255 )
        hdr  = uint8( log1p(10*raw) / max_log * 255 )
    """
    hdr_png = iio.imread(hdr_png_path)[..., :3].astype(np.float64) / 255.0
    ldr_png = iio.imread(ldr_path)[..., :3].astype(np.float64) / 255.0

    ldr_linear = ldr_png ** 2.2
    hdr_norm = hdr_png

    non_sat = (ldr_linear > 0.01) & (ldr_linear < 0.95) & (hdr_norm > 0.01)
    if non_sat.any():
        max_log = np.median(np.log1p(10.0 * ldr_linear[non_sat]) / hdr_norm[non_sat])
    else:
        max_log = np.log1p(10.0)

    raw_hdr = np.expm1(hdr_norm * max_log) / 10.0
    return raw_hdr.astype(np.float32)


def find_ldr_path(iter_dir: str, view_idx: int) -> Optional[str]:
    """Locate the LDR envmap file for a given 1-indexed view, accepting jpg/jpeg/png."""
    base = os.path.join(iter_dir, f"context_envldr_view_{view_idx:02d}")
    for ext in (".jpg", ".jpeg", ".png"):
        cand = base + ext
        if os.path.exists(cand):
            return cand
    return None


def write_exr(path: str, hdr: np.ndarray) -> None:
    """Write a float32 HDR image as a 32-bit OpenEXR file."""
    hdr = np.ascontiguousarray(hdr.astype(np.float32))
    try:
        iio.imwrite(path, hdr, extension=".exr")
        return
    except Exception:
        pass
    try:
        imageio.plugins.freeimage.download()
    except Exception:
        pass
    imageio.imwrite(path, hdr, flags=0x0001)  # PIZ compression


def prepare_envmap_exr(iter_dir: str, view_idx: int) -> str:
    """Reconstruct an HDR envmap and stage it as a tempfile ``.exr``.

    Blender's ``set_env_light`` requires an on-disk HDR file. The .exr lives in
    the system temp dir and should be removed by the caller after rendering.
    Returns the absolute path of the temp .exr.
    """
    hdr_png = os.path.join(iter_dir, f"context_envhdr_view_{view_idx:02d}.png")
    ldr_path = find_ldr_path(iter_dir, view_idx)
    if not os.path.exists(hdr_png):
        raise FileNotFoundError(f"Missing HDR png: {hdr_png}")
    if ldr_path is None:
        raise FileNotFoundError(
            f"Missing LDR file: {iter_dir}/context_envldr_view_{view_idx:02d}.(jpg|jpeg|png)"
        )

    hdr = reconstruct_hdr_from_pair(hdr_png, ldr_path)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f"sf3d_env_view_{view_idx:02d}_", suffix=".exr"
    )
    os.close(fd)
    write_exr(tmp_path, hdr)
    return os.path.abspath(tmp_path)


# --------------------------------------------------------------------------- #
# Blender rendering                                                           #
# --------------------------------------------------------------------------- #


def _configure_blender(resolution: int, cycles_samples: int) -> None:
    import bpy

    scene = bpy.context.scene
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.engine = "CYCLES"

    cprefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        cprefs.get_devices()
    except Exception:
        pass
    # GPU if available, otherwise CPU. CUDA preferred but optional.
    try:
        cprefs.compute_device_type = "CUDA"
        scene.cycles.device = "GPU"
    except Exception:
        scene.cycles.device = "CPU"

    scene.cycles.samples = cycles_samples
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"


def _render_and_premultiply(output_path: str) -> None:
    """Render the current scene to ``output_path`` and premultiply alpha."""
    import bpy

    bpy.context.scene.view_layers["ViewLayer"].material_override = None
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    bpy.context.view_layer.update()

    img = iio.imread(output_path) / 255.0
    if img.shape[-1] == 4:
        rgb = img[..., :3] * img[..., 3:]
        rgba = np.concatenate([rgb, img[..., 3:]], axis=-1)
    else:
        rgba = img
    iio.imwrite(output_path, (rgba * 255).clip(0, 255).astype(np.uint8))


def _render_one_mesh(
    mesh_path: str,
    exr_path: str,
    out_path: str,
    args: Options,
) -> None:
    """Reset Blender, load one mesh, set env light, render to ``out_path``."""
    import bpy

    from bpy_helper.camera import create_camera, look_at_to_c2w
    from bpy_helper.light import set_env_light
    from bpy_helper.scene import import_3d_model, normalize_scene, reset_scene
    from bpy_helper.utils import stdout_redirected
    from bpy_helper.material import clear_emission_and_alpha_nodes

    reset_scene()

    with stdout_redirected():
        import_3d_model(mesh_path)

    if args.normalize:
        scale, offset = normalize_scene(
            use_bounding_sphere=args.normalize_use_bounding_sphere,
            target_scale=args.normalize_target_scale,
        )
        print(
            f"  normalize: scale={float(scale):.4f} "
            f"offset=({float(offset[0]):.4f}, {float(offset[1]):.4f}, {float(offset[2]):.4f})"
        )

    clear_emission_and_alpha_nodes()

    _configure_blender(args.resolution, args.cycles_samples)

    c2w = look_at_to_c2w([0.0, 1.0, 0.0])
    camera = create_camera(c2w, fov=args.fov_deg)
    bpy.context.scene.camera = camera

    set_env_light(
        exr_path,
        strength=args.env_strength,
        rotation_euler=[0.0, 0.0, args.env_rotation_z],
    )

    with stdout_redirected():
        _render_and_premultiply(out_path)

    try:
        bpy.data.objects.remove(camera, do_unlink=True)
    except Exception:
        pass


def render_scene(scene_dir: str, args: Options) -> None:
    """Render both meshes of a single scene directory."""
    iter_dir = os.path.join(scene_dir, args.iter_subdir)
    if not os.path.isdir(iter_dir):
        # Fallback: pick the highest-numbered ``iter_*`` subdirectory.
        candidates = sorted(glob.glob(os.path.join(scene_dir, "iter_*")))
        if not candidates:
            raise FileNotFoundError(f"No iter_* subdir under {scene_dir}")
        iter_dir = candidates[-1]

    targets = []
    for mesh_idx in (0, 1):
        mesh_path = os.path.join(scene_dir, f"mesh_{mesh_idx:02d}.glb")
        if not os.path.exists(mesh_path):
            print(f"[skip] missing mesh: {mesh_path}")
            continue
        view_idx = mesh_idx + 1  # mesh_00 -> view_01, mesh_01 -> view_02
        out_path = os.path.join(
            iter_dir, f"{args.output_prefix}_{mesh_idx:02d}.png"
        )
        targets.append((mesh_idx, view_idx, mesh_path, out_path))

    if not targets:
        return

    for mesh_idx, view_idx, mesh_path, out_path in targets:
        exr_path = prepare_envmap_exr(iter_dir, view_idx)
        print(
            f"[render] {os.path.basename(scene_dir)} mesh_{mesh_idx:02d} "
            f"<- env_view_{view_idx:02d} -> {os.path.basename(out_path)}"
        )
        try:
            _render_one_mesh(mesh_path, exr_path, out_path, args)
        finally:
            try:
                os.remove(exr_path)
            except OSError:
                pass


def iter_scene_dirs(data_root: str, scene_filter: Optional[str]):
    for name in sorted(os.listdir(data_root)):
        if scene_filter is not None and scene_filter not in name:
            continue
        path = os.path.join(data_root, name)
        if not os.path.isdir(path):
            continue
        if name.startswith("."):
            continue
        yield path


def main() -> None:
    args: Options = simple_parsing.parse(Options)
    print(args)

    if not os.path.isdir(args.data_root):
        raise FileNotFoundError(f"data_root does not exist: {args.data_root}")

    error_list = []
    scene_dirs = list(iter_scene_dirs(args.data_root, args.scene_filter))
    print(f"Found {len(scene_dirs)} scene(s) under {args.data_root}")

    for idx, scene_dir in enumerate(scene_dirs):
        print(f"\n=== [{idx + 1}/{len(scene_dirs)}] {scene_dir} ===")
        try:
            render_scene(scene_dir, args)
        except Exception as e:
            traceback.print_exc()
            error_list.append((scene_dir, repr(e)))
            print(f"[error] {scene_dir}: {e}")
            continue

    if error_list:
        print(f"\nCompleted with {len(error_list)} error(s):")
        for scene_dir, err in error_list:
            print(f"  - {scene_dir}: {err}")
    else:
        print("\nAll scenes rendered successfully.")


if __name__ == "__main__":
    main()
