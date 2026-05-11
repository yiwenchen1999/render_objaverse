"""Sanity-check the camera-pose alignment used by ``render_sf3d_meshes.py``.

For a given scene directory, parse ``camera_context_view_{01,02}.json`` and
``camera_target_view_{01..08}.json``, convert them from OpenCV to OpenGL,
recover the same similarity transform ``(R, s)`` we use at render time
(so that ``camera_context_view_{anchor}.json`` lands exactly at the
Blender camera at ``(0, 1, 0)`` looking at the origin), and draw all
cameras as Open3D frusta together with the (optionally loaded) mesh.

Run locally (no Blender needed):

    python scripts/render_sf3d_mesh/visualize_cameras.py \\
        --scene_dir asset_samples/meshes_sf3d/00ab1b90e5fd453aa8706c18cbbdef1e_env_0 \\
        --iter_subdir iter_00000297 \\
        --anchor_mesh_idx 0 \\
        --load_mesh

Requires ``open3d`` (``pip install open3d``); for ``--load_mesh`` also
``trimesh``.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from typing import List, Optional, Tuple

import numpy as np

try:
    import open3d as o3d  # type: ignore[import-not-found]
    _HAS_OPEN3D = True
except ImportError:  # pragma: no cover - allow import for math sanity checks
    o3d = None  # type: ignore[assignment]
    _HAS_OPEN3D = False


# --------------------------------------------------------------------------- #
# Math helpers (mirrors of render_sf3d_meshes.py + bpy_helper.camera)         #
# --------------------------------------------------------------------------- #


def load_camera_json(path: str) -> Tuple[np.ndarray, Optional[List[float]]]:
    with open(path, "r") as f:
        data = json.load(f)
    return np.asarray(data["c2w"], dtype=np.float64), data.get("fxfycxcy")


def opencv_c2w_to_opengl(c2w: np.ndarray) -> np.ndarray:
    out = c2w.copy()
    out[:3, 1] *= -1.0
    out[:3, 2] *= -1.0
    return out


def look_at_to_c2w_blender(
    camera_position=(0.0, 1.0, 0.0),
    target=(0.0, 0.0, 0.0),
    up=(0.0, 0.0, 1.0),
) -> np.ndarray:
    """Pure-numpy port of ``bpy_helper.camera.look_at_to_c2w``."""
    p = np.asarray(camera_position, dtype=np.float64)
    t = np.asarray(target, dtype=np.float64)
    u = np.asarray(up, dtype=np.float64)

    direction = p - t
    direction /= np.linalg.norm(direction)
    right = np.cross(u, direction)
    right /= np.linalg.norm(right)
    new_up = np.cross(direction, right)
    new_up /= np.linalg.norm(new_up)

    R = np.zeros((4, 4))
    R[0, :3] = right
    R[1, :3] = new_up
    R[2, :3] = direction
    R[3, 3] = 1.0
    T = np.eye(4)
    T[:3, 3] = -p
    return np.linalg.inv(R @ T)


def closest_point_to_rays(
    origins: List[np.ndarray], directions: List[np.ndarray]
) -> np.ndarray:
    """LSQ closest-approach point of a set of rays in 3D."""
    M = np.zeros((3, 3))
    b = np.zeros(3)
    for p, d in zip(origins, directions):
        d_unit = d / np.linalg.norm(d)
        proj = np.eye(3) - np.outer(d_unit, d_unit)
        M += proj
        b += proj @ p
    return np.linalg.solve(M, b)


def estimate_lookat_center_gl(c2w_list_gl: List[np.ndarray]) -> np.ndarray:
    """Shared look-at point of OpenGL c2w cameras (forward = -R[:, 2])."""
    origins = [c[:3, 3] for c in c2w_list_gl]
    forwards = [-c[:3, 2] for c in c2w_list_gl]
    return closest_point_to_rays(origins, forwards)


def similarity_from_context(
    c2w_anchor_blender: np.ndarray,
    c2w_anchor_other_gl: np.ndarray,
    C_other: np.ndarray,
) -> Tuple[np.ndarray, float]:
    R_b = c2w_anchor_blender[:3, :3]
    R_o = c2w_anchor_other_gl[:3, :3]
    R = R_b @ R_o.T
    diff_o = c2w_anchor_other_gl[:3, 3] - C_other
    diff_b = c2w_anchor_blender[:3, 3]
    n_o = float(np.linalg.norm(diff_o))
    n_b = float(np.linalg.norm(diff_b))
    s = (n_b / n_o) if n_o > 1e-9 else 1.0
    return R, s


def apply_similarity(
    R: np.ndarray, s: float, C_other: np.ndarray, c2w_other_gl: np.ndarray
) -> np.ndarray:
    out = np.eye(4)
    out[:3, :3] = R @ c2w_other_gl[:3, :3]
    out[:3, 3] = s * (R @ (c2w_other_gl[:3, 3] - C_other))
    return out


def fov_deg_from_fxfycxcy(fxfycxcy: Optional[List[float]]) -> Optional[float]:
    if fxfycxcy is None:
        return None
    fx, _fy, cx, _cy = fxfycxcy
    img_w = 2.0 * float(cx)
    return math.degrees(2.0 * math.atan(img_w / (2.0 * float(fx))))


# --------------------------------------------------------------------------- #
# Open3D helpers                                                              #
# --------------------------------------------------------------------------- #


def make_camera_frustum(
    c2w: np.ndarray,
    fov_deg: float,
    color=(1.0, 0.0, 0.0),
    near: float = 0.12,
) -> o3d.geometry.LineSet:
    """A simple frustum LineSet in world frame; camera looks down -Z (OpenGL).

    ``near`` controls the length of the frustum (apex -> base distance).
    """
    half = near * math.tan(math.radians(fov_deg) / 2.0)
    apex_cam = np.array([0.0, 0.0, 0.0, 1.0])
    base_cam = np.array(
        [
            [-half, -half, -near, 1.0],
            [+half, -half, -near, 1.0],
            [+half, +half, -near, 1.0],
            [-half, +half, -near, 1.0],
        ]
    )
    pts_cam = np.vstack([apex_cam[None], base_cam])  # (5, 4)
    pts_world = (c2w @ pts_cam.T).T[:, :3]

    lines = [
        [0, 1], [0, 2], [0, 3], [0, 4],   # apex -> base corners
        [1, 2], [2, 3], [3, 4], [4, 1],   # base rectangle
    ]
    ls = o3d.geometry.LineSet()
    ls.points = o3d.utility.Vector3dVector(pts_world)
    ls.lines = o3d.utility.Vector2iVector(lines)
    ls.colors = o3d.utility.Vector3dVector([list(color)] * len(lines))
    return ls


def make_up_arrow(
    c2w: np.ndarray, length: float, color=(0.0, 0.0, 0.0)
) -> o3d.geometry.LineSet:
    """Thin line from camera origin along camera +Y (up) to disambiguate roll."""
    cam_o = c2w[:3, 3]
    up_world = c2w[:3, 1]
    ls = o3d.geometry.LineSet()
    ls.points = o3d.utility.Vector3dVector(np.stack([cam_o, cam_o + length * up_world]))
    ls.lines = o3d.utility.Vector2iVector([[0, 1]])
    ls.colors = o3d.utility.Vector3dVector([list(color)])
    return ls


def try_load_mesh_as_o3d(path: str) -> Optional[o3d.geometry.TriangleMesh]:
    """Best-effort glb -> Open3D TriangleMesh."""
    try:
        m = o3d.io.read_triangle_mesh(path)
        if len(m.triangles) > 0:
            m.compute_vertex_normals()
            return m
    except Exception:
        pass
    try:
        import trimesh  # type: ignore[import-not-found]

        tm = trimesh.load(path, force="mesh")
        if isinstance(tm, trimesh.Scene):
            tm = tm.dump(concatenate=True)
        verts = np.asarray(tm.vertices, dtype=np.float64)
        faces = np.asarray(tm.faces, dtype=np.int32)
        m = o3d.geometry.TriangleMesh()
        m.vertices = o3d.utility.Vector3dVector(verts)
        m.triangles = o3d.utility.Vector3iVector(faces)
        m.compute_vertex_normals()
        m.paint_uniform_color([0.7, 0.7, 0.7])
        return m
    except Exception as e:
        print(f"  could not load mesh {path}: {e}")
        return None


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #


def main() -> None:
    if not _HAS_OPEN3D:
        raise SystemExit(
            "open3d is required for visualization. Install with: pip install open3d"
        )
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--scene_dir",
        default="asset_samples/meshes_sf3d/00ab1b90e5fd453aa8706c18cbbdef1e_env_0",
    )
    ap.add_argument("--iter_subdir", default="iter_00000297")
    ap.add_argument(
        "--anchor_mesh_idx",
        type=int,
        default=0,
        choices=[0, 1],
        help="Which context camera anchors the new coord system: "
        "0 -> camera_context_view_01.json, 1 -> camera_context_view_02.json.",
    )
    ap.add_argument(
        "--load_mesh",
        action="store_true",
        help="Also draw the corresponding mesh_{anchor_mesh_idx}.glb at the origin.",
    )
    ap.add_argument(
        "--also_load_other_mesh",
        action="store_true",
        help="Also draw the other mesh (mesh_01 if anchor is 0, etc.).",
    )
    ap.add_argument("--frustum_size", type=float, default=0.15)
    args = ap.parse_args()

    scene_dir = os.path.abspath(args.scene_dir)
    iter_dir = os.path.join(scene_dir, args.iter_subdir)
    anchor_view_idx = args.anchor_mesh_idx + 1  # 1 -> view_01, 0-> view_01? see below

    # ``anchor_mesh_idx=0`` => anchor on camera_context_view_01.json
    # ``anchor_mesh_idx=1`` => anchor on camera_context_view_02.json
    anchor_view_idx = args.anchor_mesh_idx + 1

    print(f"scene_dir   = {scene_dir}")
    print(f"iter_dir    = {iter_dir}")
    print(f"anchor view = camera_context_view_{anchor_view_idx:02d}.json")

    # Blender anchor camera: (0, 1, 0) looking at origin, up=z.
    c2w_ctx_blender = look_at_to_c2w_blender((0.0, 1.0, 0.0))

    # Load every camera JSON in the iter dir (both context + all target).
    other_c2w_list_gl: List[np.ndarray] = []
    json_paths: List[Tuple[str, str]] = []
    for v in (1, 2):
        p = os.path.join(iter_dir, f"camera_context_view_{v:02d}.json")
        if os.path.exists(p):
            json_paths.append((f"ctx_{v:02d}", p))
    for k in range(1, 9):
        p = os.path.join(iter_dir, f"camera_target_view_{k:02d}.json")
        if os.path.exists(p):
            json_paths.append((f"tgt_{k:02d}", p))
    for _, p in json_paths:
        c2w_ocv, _ = load_camera_json(p)
        other_c2w_list_gl.append(opencv_c2w_to_opengl(c2w_ocv))

    # Estimate shared look-at point in the 'other' world (cameras orbit
    # around this point; it is NOT the world origin for this dataset).
    C_other = estimate_lookat_center_gl(other_c2w_list_gl)
    print(
        f"C_other (shared dataset look-at point) = "
        f"({C_other[0]:+.4f}, {C_other[1]:+.4f}, {C_other[2]:+.4f}), "
        f"|C_other|={np.linalg.norm(C_other):.4f}"
    )

    # Read anchor in 'other' world (OpenCV -> OpenGL).
    anchor_json = os.path.join(iter_dir, f"camera_context_view_{anchor_view_idx:02d}.json")
    c2w_anchor_ocv, _ = load_camera_json(anchor_json)
    c2w_anchor_gl = opencv_c2w_to_opengl(c2w_anchor_ocv)

    # Recover similarity transform.
    R, s = similarity_from_context(c2w_ctx_blender, c2w_anchor_gl, C_other)
    print("Similarity R =\n", np.array2string(R, precision=4, suppress_small=True))
    print(f"Similarity s = {s:.4f}")

    geometries: List[o3d.geometry.Geometry] = []

    # World frame + origin marker.
    geometries.append(
        o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.4)
    )
    origin = o3d.geometry.TriangleMesh.create_sphere(radius=0.02)
    origin.compute_vertex_normals()
    origin.paint_uniform_color([0.5, 0.5, 0.5])
    geometries.append(origin)

    def add_camera_from_other_json(json_path: str, color, label: str) -> Optional[np.ndarray]:
        if not os.path.exists(json_path):
            print(f"  [missing] {os.path.basename(json_path)}")
            return None
        c2w_ocv, fxfycxcy = load_camera_json(json_path)
        c2w_gl = opencv_c2w_to_opengl(c2w_ocv)
        c2w_b = apply_similarity(R, s, C_other, c2w_gl)
        fov_deg = fov_deg_from_fxfycxcy(fxfycxcy) or 30.0
        geometries.append(
            make_camera_frustum(c2w_b, fov_deg, color=color, near=args.frustum_size)
        )
        geometries.append(make_up_arrow(c2w_b, length=args.frustum_size * 0.6, color=color))
        pos = c2w_b[:3, 3]
        # Forward direction (OpenGL: -R[:, 2]); for sanity-check we expect
        # this ray to pass close to the origin in Blender world.
        fwd = -c2w_b[:3, 2]
        t_along_ray_to_closest = float(-pos @ fwd)
        closest_pt = pos + t_along_ray_to_closest * fwd
        miss = float(np.linalg.norm(closest_pt))
        print(
            f"  {label:>10s}: pos=({pos[0]:+.3f}, {pos[1]:+.3f}, {pos[2]:+.3f}) "
            f"|pos|={np.linalg.norm(pos):.3f} fov={fov_deg:.2f} "
            f"miss_origin={miss:.4f}"
        )
        return c2w_b

    # Context cameras (anchor in bright red, the other context in pink).
    print("Context cameras (after similarity):")
    for v in (1, 2):
        path = os.path.join(iter_dir, f"camera_context_view_{v:02d}.json")
        is_anchor = v == anchor_view_idx
        color = (1.0, 0.0, 0.0) if is_anchor else (1.0, 0.4, 0.6)
        label = f"ctx_{v:02d}{' *' if is_anchor else ''}"
        add_camera_from_other_json(path, color, label)

    # Target cameras coloured along a blue->green ramp by index for readability.
    print("Target cameras (after similarity):")
    for k in range(1, 9):
        path = os.path.join(iter_dir, f"camera_target_view_{k:02d}.json")
        # 1..8 -> hue ramp 0.55..0.35 ish, simple lerp blue -> green
        t = (k - 1) / 7.0
        color = (0.0, 0.3 + 0.6 * t, 1.0 - 0.6 * t)
        add_camera_from_other_json(path, color, f"tgt_{k:02d}")

    # Optional meshes.
    if args.load_mesh:
        for mi in {args.anchor_mesh_idx, 1 - args.anchor_mesh_idx if args.also_load_other_mesh else args.anchor_mesh_idx}:
            mesh_path = os.path.join(scene_dir, f"mesh_{mi:02d}.glb")
            print(f"Loading mesh: {mesh_path}")
            mesh = try_load_mesh_as_o3d(mesh_path)
            if mesh is not None:
                if mi != args.anchor_mesh_idx:
                    mesh.paint_uniform_color([0.5, 0.7, 0.5])
                geometries.append(mesh)

    print(
        "\nLegend: bright red = anchor context cam (expected exactly at (0,1,0)), "
        "pink = other context cam, blue→green ramp = target 01→08."
    )
    print("Up-direction is shown as a short stub from each camera origin.\n")

    o3d.visualization.draw_geometries(geometries, mesh_show_back_face=True)


if __name__ == "__main__":
    main()
