# Render SF3D meshes per scene

Re-renders each `mesh_00.glb` / `mesh_01.glb` under a scenes root, lit by the
matching `context_envhdr_view_{01,02}.png` + `context_envldr_view_{01,02}.jpg`
pair (reconstructed back to a linear HDR EXR on disk), from a fixed camera at
`(0, -1, 0)` looking at the origin (z-up).

## Layout assumed under `--data_root`

```
<data_root>/
  00ab1b90e5fd453aa8706c18cbbdef1e_env_0/
    mesh_00.glb
    mesh_01.glb
    iter_00000297/
      context_envhdr_view_01.png
      context_envldr_view_01.jpg
      context_envhdr_view_02.png
      context_envldr_view_02.jpg
      ...
```

`mesh_00` is paired with `view_01`, `mesh_01` with `view_02`.

## Outputs

For each scene the script writes back into the same `iter_*` subdirectory:

- `context_env_view_01.exr`, `context_env_view_02.exr` (reconstructed HDR envmaps).
- `rerender_view_00.png`, `rerender_view_01.png` (rendered images at
  `--resolution`, premultiplied RGB by alpha to suppress edge aliasing).

The two `rerender_view_*.png` files can be visually compared against the
existing `input512_view_*.png` ground-truth context views to validate the
camera / envmap setup.

## Quick smoke test

```bash
# from the repo root
bash scripts/render_sf3d_mesh/render_sf3d_mesh.sh asset_samples/meshes_sf3d

# limit to a single scene
SCENE_FILTER=00ab1b90e5fd453aa8706c18cbbdef1e_env_0 \
    bash scripts/render_sf3d_mesh/render_sf3d_mesh.sh asset_samples/meshes_sf3d

# overwrite existing rerenders
OVERWRITE=1 bash scripts/render_sf3d_mesh/render_sf3d_mesh.sh \
    asset_samples/meshes_sf3d
```

You can also invoke the Python script directly:

```bash
python render_sf3d_meshes.py \
    --data_root asset_samples/meshes_sf3d \
    --iter_subdir iter_00000297 \
    --resolution 512 \
    --fov_deg 30 \
    --cycles_samples 128
```

## Tuning knobs

| Variable           | CLI flag             | Default | Notes |
|--------------------|----------------------|---------|-------|
| `RESOLUTION`       | `--resolution`       | 512     | Square render resolution. |
| `FOV_DEG`          | `--fov_deg`          | 30      | Matches `fxfycxcy=[477.7, 477.7, 128, 128]` at 256 px (= 512 px). |
| `CYCLES_SAMPLES`   | `--cycles_samples`   | 128     | Lower while iterating; bump up for final renders. |
| `ENV_ROTATION_Z`   | `--env_rotation_z`   | 0.0     | Tweak (radians) if envmap orientation looks rotated vs. the GT. |
| `ENV_STRENGTH`     | `--env_strength`     | 1.0     | Multiplier on the env light. |
| `SCENE_FILTER`     | `--scene_filter`     | (none)  | Substring match on scene dir name. |
| `OVERWRITE`        | `--overwrite`        | off     | Re-render even if `rerender_view_*.png` exists. |

If after a smoke test the envmap orientation looks rotated 90 degrees relative
to `input512_view_*.png`, the most likely fix is
`--env_rotation_z="-1.5707963"` (i.e. `-pi/2`), which is equivalent to the
`np.roll(envmap, -w//4, axis=1)` step that
[dataset_polyhaven.py](../../dataset_polyhaven.py) applies on load.
