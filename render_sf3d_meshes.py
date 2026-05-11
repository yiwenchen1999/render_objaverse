"""Render SF3D-generated meshes per scene with the matching context envmap.

Each scene directory under ``--data_root`` is expected to contain two SF3D
mesh predictions (``mesh_00.glb``, ``mesh_01.glb``) and an iteration subdir
(default ``iter_00000297``) holding paired HDR/LDR encoded envmap pngs and
the camera JSONs.

For each mesh we:
    1. Reconstruct the HDR envmap from the (hdr_png, ldr_png) pair (mirroring
       ``dataset_polyhaven.reconstruct_hdr_from_pngs``) and stage it as a
       temporary ``.exr`` so Blender can load it; the temp file is removed
       once the render is done.
    2. Load the glb. Optionally normalize with ``normalize_scene(...)`` when
       ``--normalize`` is set (bounding sphere radius ``--target_scale``).
       By default the mesh stays as-imported scale/position.
    3. Render the **context view** with a Blender camera fixed at
       ``(0, 1, 0)`` looking at the origin (up=z), saved as
       ``rerender_view_{00,01}.png``.
    4. Render the **target/novel views**: parse
       ``camera_context_view_{01,02}.json`` and
       ``camera_target_view_{01..08}.json`` (OpenCV c2w + fxfycxcy in some
       other world frame). For each mesh, derive a similarity transform
       (R, s) from its context cameras (other-world OpenGL <-> blender-world
       OpenGL), apply it to every target c2w, and render to
       ``target_view_{mesh_idx}_{k}.png`` (k = 0..7). The same envmap is used
       for both context and targets; by default we also rotate the world
       envmap by R so the lighting direction stays consistent with the
       dataset (override via ``--no_align_env``).
"""

import glob
import json
import math
import os
import sys
import tempfile
import traceback
from dataclasses import dataclass
from typing import List, Optional, Tuple

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
    env_rotation_z: float = 0.0  # extra Z-axis offset applied on top of R
    env_strength: float = 1.0
    normalize: bool = False  # if True, bbox-sphere normalization after import
    target_scale: float = 0.2  # bounding-sphere radius when normalize is True
    scene_filter: Optional[str] = None
    output_prefix: str = "rerender_view"
    target_prefix: str = "target_view"
    num_target_views: int = 8
    skip_target_views: bool = False
    # If True, rotate the env light by the world-rotation R derived from
    # context cameras so the lighting direction stays consistent with the
    # dataset. Disable to keep the env in identity Blender-world orientation.
    align_env: bool = True


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
# Camera / similarity helpers                                                 #
# --------------------------------------------------------------------------- #


def _load_camera_json(path: str) -> Tuple[np.ndarray, Optional[List[float]]]:
    """Read a camera JSON and return (c2w 4x4 ndarray, [fx, fy, cx, cy])."""
    with open(path, "r") as f:
        data = json.load(f)
    c2w = np.asarray(data["c2w"], dtype=np.float64)
    fxfycxcy = data.get("fxfycxcy")
    return c2w, fxfycxcy


def _opencv_c2w_to_opengl(c2w: np.ndarray) -> np.ndarray:
    """Convert a c2w from OpenCV camera convention to OpenGL/Blender.

    OpenCV: +X right, +Y down, +Z forward.
    OpenGL: +X right, +Y up,   -Z forward.
    The world frame is unchanged. We flip the Y and Z basis vectors of the
    camera (columns 1 and 2 of c2w); translation (column 3) is unchanged.
    """
    out = np.asarray(c2w, dtype=np.float64).copy()
    out[:3, 1] *= -1.0
    out[:3, 2] *= -1.0
    return out


def _fov_deg_from_fxfycxcy(fxfycxcy: Optional[List[float]]) -> Optional[float]:
    """Recover horizontal FoV in degrees from intrinsics, assuming centered cx."""
    if fxfycxcy is None:
        return None
    fx, _fy, cx, _cy = fxfycxcy
    img_w = 2.0 * float(cx)
    return math.degrees(2.0 * math.atan(img_w / (2.0 * float(fx))))


def _closest_point_to_rays(
    origins: List[np.ndarray], directions: List[np.ndarray]
) -> np.ndarray:
    """Least-squares closest point to a set of rays in 3D.

    Each ray is (origin, direction). Direction does not need to be unit.
    Solves ``argmin_X sum_i || (I - d_i d_i^T) (X - p_i) ||^2``.
    """
    M = np.zeros((3, 3), dtype=np.float64)
    b = np.zeros(3, dtype=np.float64)
    for p, d in zip(origins, directions):
        d_unit = np.asarray(d, dtype=np.float64)
        n = float(np.linalg.norm(d_unit))
        if n < 1e-9:
            continue
        d_unit = d_unit / n
        proj = np.eye(3) - np.outer(d_unit, d_unit)
        M += proj
        b += proj @ np.asarray(p, dtype=np.float64)
    return np.linalg.solve(M, b)


def _estimate_lookat_center_gl(c2w_list_gl: List[np.ndarray]) -> np.ndarray:
    """Closest-approach point of all camera forward rays (OpenGL c2w).

    In OpenGL, the camera looks down -Z so ``forward = -c2w[:, 2]``.
    Returns the 3D point that all cameras (approximately) look at.
    """
    origins = [np.asarray(c, dtype=np.float64)[:3, 3] for c in c2w_list_gl]
    forwards = [-np.asarray(c, dtype=np.float64)[:3, 2] for c in c2w_list_gl]
    return _closest_point_to_rays(origins, forwards)


def _similarity_from_context(
    c2w_ctx_blender: np.ndarray,
    c2w_ctx_other_gl: np.ndarray,
    C_other: np.ndarray,
) -> Tuple[np.ndarray, float]:
    """Compute (R, s) such that for any 'other' OpenGL camera c2w_other_gl,
    the equivalent Blender-world c2w_blender (with mesh at origin in Blender)
    is:

        R_blender = R @ R_other
        t_blender = s * R @ (t_other - C_other)

    Applied to the anchor (context) camera, this recovers
    ``c2w_ctx_blender`` exactly (provided the anchor in 'other' world also
    looks at ``C_other``, which is the shared look-at point of all dataset
    cameras).
    """
    c2w_b = np.asarray(c2w_ctx_blender, dtype=np.float64)
    c2w_o = np.asarray(c2w_ctx_other_gl, dtype=np.float64)
    C_o = np.asarray(C_other, dtype=np.float64)
    R = c2w_b[:3, :3] @ c2w_o[:3, :3].T
    diff_o = c2w_o[:3, 3] - C_o
    diff_b = c2w_b[:3, 3]  # C_blender = origin
    n_o = float(np.linalg.norm(diff_o))
    n_b = float(np.linalg.norm(diff_b))
    s = (n_b / n_o) if n_o > 1e-9 else 1.0
    return R, s


def _apply_similarity(
    R: np.ndarray,
    s: float,
    C_other: np.ndarray,
    c2w_other_gl: np.ndarray,
) -> np.ndarray:
    """Apply the (R, s, C_other) similarity to a c2w in 'other' OpenGL frame.

    Equivalent to translating the 'other' world so ``C_other`` is at the
    origin, then rotating by ``R`` and scaling translations by ``s``.
    """
    c2w_o = np.asarray(c2w_other_gl, dtype=np.float64)
    C_o = np.asarray(C_other, dtype=np.float64)
    out = np.eye(4, dtype=np.float64)
    out[:3, :3] = R @ c2w_o[:3, :3]
    out[:3, 3] = s * (R @ (c2w_o[:3, 3] - C_o))
    return out


def _euler_xyz_from_R(R: np.ndarray) -> Tuple[float, float, float]:
    """Decompose a 3x3 rotation matrix into Blender 'XYZ' Euler angles (radians)."""
    from mathutils import Matrix as MMatrix  # type: ignore[import-not-found]

    m4 = MMatrix.Identity(4)
    for i in range(3):
        for j in range(3):
            m4[i][j] = float(R[i][j])
    e = m4.to_euler("XYZ")
    return (float(e.x), float(e.y), float(e.z))


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


def _render_one_mesh_views(
    mesh_path: str,
    exr_path: str,
    env_rotation_euler: Tuple[float, float, float],
    views: List[Tuple[str, np.ndarray, float, str]],
    args: Options,
) -> None:
    """Load one mesh + env light once, then render every view in ``views``.

    Each entry in ``views`` is ``(label, c2w_4x4_blender, fov_deg, out_path)``.
    """
    import bpy

    from bpy_helper.camera import create_camera
    from bpy_helper.light import set_env_light
    from bpy_helper.scene import import_3d_model, normalize_scene, reset_scene
    from bpy_helper.utils import stdout_redirected
    from bpy_helper.material import clear_emission_and_alpha_nodes

    reset_scene()

    with stdout_redirected():
        import_3d_model(mesh_path)

    if args.normalize:
        # IMPORTANT: normalize_scene multiplies obj.scale and translates every
        # root object in the scene (see bpy_helper/scene.py::scene_root_objects).
        # Run it before creating camera/world extras so imported mesh roots
        # are normalized and the camera stays independent.
        assert not any(o.type == "CAMERA" for o in bpy.data.objects), (
            "normalize_scene must run before camera creation; "
            "found a CAMERA object before normalization."
        )
        assert not any(o.type == "LIGHT" for o in bpy.data.objects), (
            "normalize_scene must run before light creation; "
            "found a LIGHT object before normalization."
        )

        scale, offset = normalize_scene(
            use_bounding_sphere=True, target_scale=args.target_scale
        )
        print(
            f"  normalize_scene: scale={scale:.4f}, offset=({offset.x:.4f}, "
            f"{offset.y:.4f}, {offset.z:.4f}), target_sphere_radius={args.target_scale}"
        )
    else:
        print("  normalize_scene: skipped (mesh as-imported).")

    clear_emission_and_alpha_nodes()

    _configure_blender(args.resolution, args.cycles_samples)

    set_env_light(
        exr_path,
        strength=args.env_strength,
        rotation_euler=list(env_rotation_euler),
    )

    for label, c2w, fov_deg, out_path in views:
        camera = create_camera(c2w, fov=fov_deg)
        bpy.context.scene.camera = camera
        print(
            f"    [{label}] fov={fov_deg:.2f} deg -> {os.path.basename(out_path)}"
        )
        with stdout_redirected():
            _render_and_premultiply(out_path)
        try:
            bpy.data.objects.remove(camera, do_unlink=True)
        except Exception:
            pass


def _build_views_for_mesh(
    iter_dir: str,
    mesh_idx: int,
    view_idx: int,
    args: Options,
) -> Tuple[List[Tuple[str, np.ndarray, float, str]], Tuple[float, float, float]]:
    """Return (views, env_rotation_euler) for one mesh.

    ``views`` always starts with the fixed-Blender context view and is then
    extended with target views derived from the per-scene camera JSONs.
    ``env_rotation_euler`` is the rotation_euler to feed to ``set_env_light``;
    by default it encodes the world-rotation R recovered from the context
    cameras so the lighting stays aligned with the dataset.
    """
    from bpy_helper.camera import look_at_to_c2w

    # Context view in Blender: fixed camera at (0, 1, 0) -> origin.
    c2w_ctx_blender = np.asarray(
        look_at_to_c2w([0.0, 1.0, 0.0]), dtype=np.float64
    )

    ctx_out = os.path.join(iter_dir, f"{args.output_prefix}_{mesh_idx:02d}.png")
    views: List[Tuple[str, np.ndarray, float, str]] = [
        ("ctx", c2w_ctx_blender, float(args.fov_deg), ctx_out)
    ]

    # ------------------------------------------------------------------
    # Envmap rotation.
    #
    # The HDR envmap in this dataset is sampled in the **anchor camera's**
    # local frame (a direction d_cam in camera space picks a pixel in the
    # envmap). Blender's ``ShaderNodeTexEnvironment`` samples in the
    # **world** frame, so the mapping-node rotation must convert
    # ``d_world -> d_cam``: that is exactly ``R_anchor_w2c = R_anchor_c2w.T``.
    # This depends only on the fixed Blender anchor camera (here
    # ``(0, 1, 0)`` looking at the origin) -- NOT on the dataset->Blender
    # similarity rotation ``R``, since the envmap is anchored to the
    # camera, not to the dataset world.
    # ------------------------------------------------------------------
    if args.align_env:
        rx0, ry0, rz0 = _euler_xyz_from_R(c2w_ctx_blender[:3, :3].T)
    else:
        rx0, ry0, rz0 = 0.0, 0.0, 0.0
    env_rotation_euler: Tuple[float, float, float] = (
        rx0,
        ry0,
        rz0 + float(args.env_rotation_z),
    )

    if args.skip_target_views:
        print("  target views: skipped (--skip_target_views).")
        return views, env_rotation_euler

    ctx_json = os.path.join(
        iter_dir, f"camera_context_view_{view_idx:02d}.json"
    )
    if not os.path.exists(ctx_json):
        print(f"  [target] missing {os.path.basename(ctx_json)}; skipping novel views")
        return views, env_rotation_euler

    # ------------------------------------------------------------------
    # Load every camera JSON we'll need (both context cams + N targets)
    # so we can estimate the shared look-at point ``C_other``. Cameras in
    # this dataset orbit around ``(0, 0, ~0.79)`` in their world, not the
    # world origin, so we must center on ``C_other`` before applying R, s.
    # ------------------------------------------------------------------
    c2w_others_gl: List[np.ndarray] = []
    c2w_ctx_other_ocv, _ = _load_camera_json(ctx_json)
    c2w_ctx_other_gl = _opencv_c2w_to_opengl(c2w_ctx_other_ocv)
    c2w_others_gl.append(c2w_ctx_other_gl)

    # Also include the *other* mesh's context camera if available, plus every
    # target camera; this stabilises the C_other estimate.
    for v in (1, 2):
        if v == view_idx:
            continue
        p = os.path.join(iter_dir, f"camera_context_view_{v:02d}.json")
        if os.path.exists(p):
            c2w_o, _ = _load_camera_json(p)
            c2w_others_gl.append(_opencv_c2w_to_opengl(c2w_o))

    target_payload: List[Tuple[int, np.ndarray, Optional[List[float]]]] = []
    for k in range(1, args.num_target_views + 1):
        tgt_json = os.path.join(iter_dir, f"camera_target_view_{k:02d}.json")
        if not os.path.exists(tgt_json):
            print(f"  [target] missing {os.path.basename(tgt_json)}; skipping")
            continue
        c2w_tgt_ocv, fxfycxcy_tgt = _load_camera_json(tgt_json)
        c2w_tgt_gl = _opencv_c2w_to_opengl(c2w_tgt_ocv)
        c2w_others_gl.append(c2w_tgt_gl)
        target_payload.append((k, c2w_tgt_gl, fxfycxcy_tgt))

    C_other = _estimate_lookat_center_gl(c2w_others_gl)
    R, s = _similarity_from_context(c2w_ctx_blender, c2w_ctx_other_gl, C_other)
    print(
        f"  similarity (other -> blender world): "
        f"scale={s:.4f}, C_other=({C_other[0]:+.4f}, "
        f"{C_other[1]:+.4f}, {C_other[2]:+.4f}), "
        f"|t_anchor_other - C_other|={np.linalg.norm(c2w_ctx_other_gl[:3, 3] - C_other):.4f}"
    )

    # Sanity: the anchor must round-trip back to t_blender = (0, 1, 0).
    anchor_recovered = _apply_similarity(R, s, C_other, c2w_ctx_other_gl)
    pos_err = float(np.linalg.norm(anchor_recovered[:3, 3] - c2w_ctx_blender[:3, 3]))
    if pos_err > 1e-3:
        print(
            f"  [warn] anchor recovery error = {pos_err:.4e} "
            f"(expected ~0); look-at estimation may be off"
        )

    # env_rotation_euler was already computed above from c2w_ctx_blender;
    # log it here so per-scene output stays informative.
    if args.align_env:
        print(
            f"  env rotation (XYZ, rad): ({rx0:+.4f}, {ry0:+.4f}, "
            f"{rz0:+.4f}) + z_offset={args.env_rotation_z:+.4f} "
            "[anchor camera-frame -> world]"
        )
    else:
        print(
            f"  env rotation: (0, 0, {args.env_rotation_z:+.4f}) "
            "[--no-align-env: camera-frame rotation skipped]"
        )

    for k, c2w_tgt_gl, fxfycxcy_tgt in target_payload:
        c2w_tgt_blender = _apply_similarity(R, s, C_other, c2w_tgt_gl)
        fov_tgt = _fov_deg_from_fxfycxcy(fxfycxcy_tgt) or float(args.fov_deg)
        out_tgt = os.path.join(
            iter_dir, f"{args.target_prefix}_{mesh_idx}_{k - 1}.png"
        )
        views.append((f"tgt_{k - 1}", c2w_tgt_blender, fov_tgt, out_tgt))

    return views, env_rotation_euler


def render_scene(scene_dir: str, args: Options) -> None:
    """Render both meshes (context + target views) for one scene directory."""
    iter_dir = os.path.join(scene_dir, args.iter_subdir)
    if not os.path.isdir(iter_dir):
        # Fallback: pick the highest-numbered ``iter_*`` subdirectory.
        candidates = sorted(glob.glob(os.path.join(scene_dir, "iter_*")))
        if not candidates:
            raise FileNotFoundError(f"No iter_* subdir under {scene_dir}")
        iter_dir = candidates[-1]

    mesh_jobs = []
    for mesh_idx in (0, 1):
        mesh_path = os.path.join(scene_dir, f"mesh_{mesh_idx:02d}.glb")
        if not os.path.exists(mesh_path):
            print(f"[skip] missing mesh: {mesh_path}")
            continue
        view_idx = mesh_idx + 1  # mesh_00 -> view_01, mesh_01 -> view_02
        mesh_jobs.append((mesh_idx, view_idx, mesh_path))

    if not mesh_jobs:
        return

    for mesh_idx, view_idx, mesh_path in mesh_jobs:
        exr_path = prepare_envmap_exr(iter_dir, view_idx)
        views, env_euler = _build_views_for_mesh(
            iter_dir, mesh_idx, view_idx, args
        )
        print(
            f"[render] {os.path.basename(scene_dir)} mesh_{mesh_idx:02d} "
            f"<- env_view_{view_idx:02d} ({len(views)} view(s))"
        )
        try:
            _render_one_mesh_views(mesh_path, exr_path, env_euler, views, args)
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
