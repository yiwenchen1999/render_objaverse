# Render SF3D meshes per scene

Re-renders each `mesh_00.glb` / `mesh_01.glb` under a scenes root, lit by the
matching `context_envhdr_view_{01,02}.png` + `context_envldr_view_{01,02}.jpg`
pair (reconstructed back to a linear HDR EXR on disk).

For each mesh we render:

- one **context view** from a fixed Blender camera at `(0, 1, 0)` looking at
  the origin (z-up).
- 8 **target / novel views** derived from `camera_context_view_{01,02}.json`
  + `camera_target_view_{01..08}.json` (OpenCV `c2w` + `fxfycxcy`). The
  context cameras define a similarity transform `(R, s)` that maps the
  dataset's "other" world to the Blender world such that the context camera
  lands at `(0, 1, 0)` and distances are normalised — every target camera is
  then placed using the same similarity. The envmap is rotated by `R` so the
  lighting direction stays aligned with the dataset.

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

Meshes are loaded **as-imported** (no scale/center normalization) unless you
pass `--normalize`. With `--normalize`, `normalize_scene` fits root objects
into a bounding sphere at the origin (`--target_scale`, default `0.2`). The
camera is created only after optional normalization so it is never rescaled.

## Outputs

For each scene the script writes back into the same `iter_*` subdirectory:

- `rerender_view_00.png`, `rerender_view_01.png` — context views (mesh_00 lit
  by env-view-01; mesh_01 lit by env-view-02). Premultiplied RGB.
- `target_view_0_0.png` … `target_view_0_7.png` — 8 novel views of `mesh_00`
  at the positions derived from `camera_target_view_{01..08}.json` relative
  to `camera_context_view_01.json`.
- `target_view_1_0.png` … `target_view_1_7.png` — 8 novel views of `mesh_01`,
  same but relative to `camera_context_view_02.json`.

The reconstructed HDR envmap is staged as a temp `.exr` only for the duration
of the Blender render and removed afterwards — no `.exr` files are left in
the scene directory. Existing PNG files are **always overwritten**.

The two `rerender_view_*.png` files can be visually compared against the
existing `input512_view_*.png` ground-truth context views to validate the
camera / envmap setup. Target views can be compared against
`view_0K_gt.jpg` / `view_0K_relit_gt.jpg` if present.

## Quick smoke test

```bash
# from the repo root
bash scripts/render_sf3d_mesh/render_sf3d_mesh.sh asset_samples/meshes_sf3d

# limit to a single scene
SCENE_FILTER=00ab1b90e5fd453aa8706c18cbbdef1e_env_0 \
    bash scripts/render_sf3d_mesh/render_sf3d_mesh.sh asset_samples/meshes_sf3d

# optional: bounding-sphere normalization (radius TARGET_SCALE)
NORMALIZE=1 TARGET_SCALE=0.2 bash scripts/render_sf3d_mesh/render_sf3d_mesh.sh asset_samples/meshes_sf3d

# context views only (skip the 8 novel views)
SKIP_TARGET_VIEWS=1 bash scripts/render_sf3d_mesh/render_sf3d_mesh.sh asset_samples/meshes_sf3d

# keep env in identity orientation (do not apply world rotation R)
NO_ALIGN_ENV=1 bash scripts/render_sf3d_mesh/render_sf3d_mesh.sh asset_samples/meshes_sf3d
```

You can also invoke the Python script directly:

```bash
python render_sf3d_meshes.py \
    --data_root asset_samples/meshes_sf3d \
    --iter_subdir iter_00000297 \
    --resolution 512 \
    --fov_deg 30 \
    --cycles_samples 128

# optional bounding-sphere normalization (omit by default — mesh stays as-imported)
python render_sf3d_meshes.py \
    --data_root asset_samples/meshes_sf3d \
    --normalize \
    --target_scale 0.2
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
| `NORMALIZE`        | `--normalize`        | off     | Fit mesh roots to bounding sphere (see `--target_scale`). |
| `TARGET_SCALE`     | `--target_scale`     | 0.2     | Bounding-sphere radius when `--normalize`. |
| `NUM_TARGET_VIEWS` | `--num_target_views` | 8       | Number of `camera_target_view_*.json` files to render per mesh. |
| `SKIP_TARGET_VIEWS`| `--skip_target_views`| off     | Render only the context view per mesh. |
| `NO_ALIGN_ENV`     | `--align_env=False`  | off     | Disable rotating the envmap by the derived world rotation `R`. |

If after a smoke test the envmap orientation still looks rotated 90 degrees
relative to `input512_view_*.png`, the most likely fix is to add
`--env_rotation_z="-1.5707963"` (i.e. `-pi/2`), which is equivalent to the
`np.roll(envmap, -w//4, axis=1)` step that
[dataset_polyhaven.py](../../dataset_polyhaven.py) applies on load. This
offset is applied **in addition** to the per-mesh world rotation `R` (unless
`--align_env=False` is set).
