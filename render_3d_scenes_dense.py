import json
import math
import os
from dataclasses import dataclass
import random
from typing import Optional
import sys
import glob
import shutil

import imageio
import numpy as np
import simple_parsing
import bpy
from mathutils import Matrix, Vector

# Add current directory to path to import local modules
sys.path.append(os.getcwd())

from bpy_helper.camera import create_camera, look_at_to_c2w
from bpy_helper.io import render_depth_map, mat2list, array2list, render_normal_map, render_albedo_map, transform_normals_to_camera_space
from bpy_helper.light import create_point_light, set_env_light, create_area_light
from bpy_helper.material import create_white_diffuse_material, create_specular_ggx_material, clear_emission_and_alpha_nodes
from bpy_helper.random import gen_random_pts_around_origin, gen_pt_traj_around_origin
from bpy_helper.scene import import_3d_model, reset_scene, scene_bbox, scene_sphere
from bpy_helper.utils import stdout_redirected

error_list = []

@dataclass
class Options:
    """ 3D scene rendering script """
    # Base path to 3D models (objaverse)
    dataset_path: str = '/projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/'
    env_map_list_json: str = './assets/hdri/polyhaven_hdris.json'
    env_map_dir_path: str = '/projects/vig/Datasets/objaverse/envmaps/hdris'
    white_env_map_dir_path: str = '/projects/vig/Datasets/objaverse/envmaps/hdris'
    output_dir: str = './output_scenes'
    
    # Scene generation params
    num_objects_per_scene: int = 3
    asset_samples_dir: str = '/projects/vig/Datasets/Polyhaven'
    textures_path: str = '/projects/vig/Datasets/Polyhaven/textures'
    
    num_views: int = 5
    num_test_views: int = 5
    num_white_pls: int = 0
    num_rgb_pls: int = 0
    num_multi_pls: int = 0
    max_pl_num: int = 0
    num_white_envs: int = 1
    num_env_lights: int = 1
    num_area_lights: int = 0
    seed: Optional[int] = None
    num_view_groups: int = 1
    group_start: int = 0
    group_end: int = 2
    save_intrinsics: bool = True
    csv_path: str = "test_obj.csv"
    rendered_dir_name: str = "rendered_scenes_dense"

def load_texture_to_plane(plane_obj, texture_path):
    """Load a material from a blend file and apply it to the plane."""
    with bpy.data.libraries.load(texture_path) as (data_from, data_to):
        # Load all materials
        data_to.materials = data_from.materials
    
    if data_to.materials:
        # Pick the first material
        mat = data_to.materials[0]
        if plane_obj.data.materials:
            plane_obj.data.materials[0] = mat
        else:
            plane_obj.data.materials.append(mat)
        return True
    return False

def normalize_object(obj_root, target_scale=0.5):
    """
    Normalize a single object (hierarchy rooted at obj_root) to fit in a sphere of radius target_scale.
    """
    bbox_min = Vector((math.inf, math.inf, math.inf))
    bbox_max = Vector((-math.inf, -math.inf, -math.inf))
    
    descendants = obj_root.children_recursive + [obj_root]
    meshes = [o for o in descendants if o.type == 'MESH']
    
    if not meshes:
        return 1.0, Vector((0,0,0)), bbox_min, bbox_max

    for obj in meshes:
        for coord in obj.bound_box:
            coord = Vector(coord)
            coord = obj.matrix_world @ coord
            bbox_min = Vector((min(bbox_min.x, coord.x), min(bbox_min.y, coord.y), min(bbox_min.z, coord.z)))
            bbox_max = Vector((max(bbox_max.x, coord.x), max(bbox_max.y, coord.y), max(bbox_max.z, coord.z)))
            
    # Calculate scale
    radius = max((bbox_max - bbox_min)) / 2
    
    if radius < 1e-6:
        scale = 1.0
    else:
        scale = target_scale / radius
        
    # Apply scale
    obj_root.scale *= scale
    bpy.context.view_layer.update()
    
    # Recalculate center offset to (0,0,0)
    center = (bbox_min + bbox_max) / 2 * scale # Approximate center after scaling
    # Better: re-measure bbox
    
    # Apply translation to root to center it
    # We want geometric center at (0,0,0) locally
    # Actually, simpler: just calculate offset to move 'center' to (0,0,0)
    # But wait, bbox_min/max were in world space (which is root space since root is at 0,0,0)
    # So center is the vector from root to bbox center.
    offset = -(bbox_min + bbox_max) / 2
    
    obj_root.matrix_world.translation += offset
    bpy.context.view_layer.update()
    
    return scale, offset, bbox_min, bbox_max

def render_core(args: Options, scene_idx: int, selected_objects: list, group_id: int = 0):
    
    def render_rgb_and_hint(output_path, idx=0):
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.filepath = os.path.join(output_path, f'gt_{idx}.png')
        bpy.ops.render.render(write_still=True)
        
        img = imageio.v3.imread(os.path.join(output_path, f'gt_{idx}.png')) / 255.
        if img.shape[-1] == 4:
            img = img[..., :3] * img[..., 3:]
        imageio.v3.imwrite(os.path.join(output_path, f'gt_{idx}.png'), (img * 255).clip(0, 255).astype(np.uint8))

    def configure_blender():
        bpy.context.scene.render.resolution_x = 512
        bpy.context.scene.render.resolution_y = 512
        bpy.context.scene.render.engine = 'CYCLES'
        preferences = bpy.context.preferences
        cycles_preferences = preferences.addons["cycles"].preferences
        cycles_preferences.get_devices()
        cycles_preferences.compute_device_type = "CUDA"
        bpy.context.scene.cycles.device = "GPU"
        bpy.context.scene.render.film_transparent = True
        bpy.context.scene.render.image_settings.color_mode = 'RGBA'

    reset_scene()
    configure_blender()

    # --- 1. Scene Setup ---
    
    # 1.1 Ground Plane
    bpy.ops.mesh.primitive_plane_add(size=50, location=(0, 0, 0))
    ground_plane = bpy.context.active_object
    ground_plane.name = "GroundPlane"
    
    textures_dir = args.textures_path
    texture_files = glob.glob(os.path.join(textures_dir, '*.blend'))
    tex_path = None
    if texture_files:
        tex_path = random.choice(texture_files)
        load_texture_to_plane(ground_plane, tex_path)
    
    ground_plane.rotation_euler[2] = random.uniform(0, 2 * math.pi)
    
    # 1.2 Import and Place Objects
    scene_objects_info = []
    
    for i, (index, uid) in enumerate(selected_objects):
        model_path = os.path.join(args.dataset_path, index, f'{uid}.glb')
        existing_objs = set(bpy.context.scene.objects)
        
        with stdout_redirected():
            try:
                import_3d_model(model_path)
            except Exception as e:
                print(f"Failed to load model {uid}: {e}")
                continue
                
        new_objs = list(set(bpy.context.scene.objects) - existing_objs)
        if not new_objs:
            continue
            
        root_empty = bpy.data.objects.new(f"Object_{i}_{uid}", None)
        bpy.context.scene.collection.objects.link(root_empty)
        for obj in new_objs:
            if obj.parent is None:
                obj.parent = root_empty
        
        scale, offset, bbox_min, bbox_max = normalize_object(root_empty, target_scale=0.5)
        
        # Place object
        r = random.uniform(0, 2.0)
        theta = random.uniform(0, 2 * math.pi)
        x = r * math.cos(theta)
        y = r * math.sin(theta)
        
        # Calculate min z to place on ground
        min_z = math.inf
        for obj in new_objs:
            if obj.type == 'MESH':
                for v in obj.bound_box:
                    world_v = obj.matrix_world @ Vector(v)
                    if world_v.z < min_z:
                        min_z = world_v.z
        if min_z == math.inf: min_z = 0
        z_translation = -min_z
        
        root_empty.location = Vector((x, y, z_translation))
        root_empty.rotation_euler[2] = random.uniform(0, 2 * math.pi)
        
        scene_objects_info.append({
            'uid': uid,
            'scale': scale,
            'location': array2list(root_empty.location),
            'rotation': array2list(root_empty.rotation_euler)
        })

    clear_emission_and_alpha_nodes()
    
    # --- 2. Lighting & Rendering ---
    
    env_map_list = json.load(open(args.env_map_list_json, 'r'))
    
    seed_view = None if args.seed is None else args.seed + scene_idx
    seed_white_pl = None if args.seed is None else args.seed + scene_idx + 1
    seed_rgb_pl = None if args.seed is None else args.seed + scene_idx + 2
    seed_multi_pl = None if args.seed is None else args.seed + scene_idx + 3
    seed_area = None if args.seed is None else args.seed + scene_idx + 4
    
    res_dir = os.path.join(args.output_dir, f"scene_{scene_idx:06d}")
    os.makedirs(res_dir, exist_ok=True)
    
    json.dump({
        'objects': scene_objects_info,
        'ground_texture': os.path.basename(tex_path) if tex_path else None
    }, open(f'{res_dir}/scene_info.json', 'w'), indent=4)
    
    json.dump({'scale': 1.0, 'offset': [0, 0, 0]}, open(f'{res_dir}/normalize.json', 'w'), indent=4)

    eyes = gen_random_pts_around_origin(
        seed=seed_view,
        N=args.num_views,
        min_dist_to_origin=3.0,
        max_dist_to_origin=4.5,
        min_theta_in_degree=0,
        max_theta_in_degree=80,
        z_up=True
    )
    eyes_traj = gen_pt_traj_around_origin(
        seed=seed_view,
        N=args.num_test_views,
        min_dist_to_origin=4.0,
        max_dist_to_origin=4.0,
        theta_in_degree=60,
        z_up=True
    )
    
    cameras = []
    cameras_test = []
    for eye_idx, eye in enumerate(eyes):
        fov = 40
        c2w = look_at_to_c2w(eye)
        cameras.append((eye_idx, c2w, fov))

    for eye_idx, eye in enumerate(eyes_traj):
        fov = 40
        c2w = look_at_to_c2w(eye)
        cameras_test.append((eye_idx, c2w, fov))

    intrinsics_saved = not args.save_intrinsics

    def is_folder_populated(path, num_expected):
        if os.path.exists(path + '.tar'): return True
        if not os.path.exists(path): return False
        png_files = glob.glob(os.path.join(path, '*.png'))
        return len(png_files) >= num_expected

    def render_views(view_type, env_path, cams):
        for eye_idx, c2w, fov in cams:
            camera = create_camera(c2w, fov)
            bpy.context.scene.camera = camera
            view_path = f'{res_dir}/{view_type}'
            os.makedirs(view_path, exist_ok=True)
            
            nonlocal intrinsics_saved
            if not intrinsics_saved:
                with stdout_redirected():
                    render_depth_map(view_path, file_prefix=f'depth_{eye_idx}')
                    render_normal_map(view_path)
                    render_albedo_map(view_path)
                
                os.makedirs(os.path.join(view_path, 'depth'), exist_ok=True)
                shutil.copy(os.path.join(view_path, f'depth_{eye_idx}0001.exr'), os.path.join(view_path, 'depth', f'depth_{eye_idx}.exr'))
                
                os.makedirs(os.path.join(view_path, 'normal'), exist_ok=True)
                transform_normals_to_camera_space(os.path.join(view_path, 'normal0001.exr'), c2w, os.path.join(view_path, 'normal', f'normal_cam_{eye_idx}.exr'))
                
                os.makedirs(os.path.join(view_path, 'albedo'), exist_ok=True)
                shutil.copy(os.path.join(view_path, 'albedo0001.png'), os.path.join(view_path, 'albedo', f'albedo_cam_{eye_idx}.png'))
                
                for f in [f'depth_{eye_idx}0001.exr', 'normal0001.exr', 'albedo0001.png']:
                    if os.path.exists(os.path.join(view_path, f)): os.remove(os.path.join(view_path, f))
                for f in os.listdir(view_path):
                    if f.startswith('rgb_for_'): os.remove(os.path.join(view_path, f))

            _env_path = f'{view_path}/{env_path}'
            os.makedirs(_env_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{_env_path}', eye_idx)
            bpy.data.objects.remove(camera, do_unlink=True)
        
        # Save cameras.json only once per view_type
        cam_data = [{'eye_idx': i, 'c2w': mat2list(c), 'fov': f} for i, c, f in cams]
        json.dump(cam_data, open(os.path.join(f'{res_dir}/{view_type}', 'cameras.json'), 'w'), indent=4)

    # 2.1 White Env
    for env_idx in range(args.num_white_envs):
        if is_folder_populated(f'{res_dir}/train/white_env_{env_idx}', len(cameras)): continue
        env_map_path = f'{args.white_env_map_dir_path}/white_env_8k.exr'
        set_env_light(env_map_path, rotation_euler=[0, 0, random.uniform(-math.pi, math.pi)], strength=1.0)
        render_views('train', f'white_env_{env_idx}', cameras)
        render_views('test', f'white_env_{env_idx}', cameras_test)
        intrinsics_saved = True

    # 2.2 White PL
    white_pls = gen_random_pts_around_origin(seed=seed_white_pl, N=args.num_white_pls, min_dist_to_origin=3.5, max_dist_to_origin=5.0, min_theta_in_degree=0, max_theta_in_degree=85)
    for idx in range(args.num_white_pls):
        if is_folder_populated(f'{res_dir}/train/white_pl_{idx}', len(cameras)): continue
        pl = white_pls[idx]
        power = random.uniform(500, 1500)
        create_point_light(pl, power)
        render_views('train', f'white_pl_{idx}', cameras)
        render_views('test', f'white_pl_{idx}', cameras_test)
        json.dump({'pos': array2list(pl), 'power': power}, open(f'{res_dir}/train/white_pl_{idx}/white_pl.json', 'w'), indent=4)

    # 2.3 RGB PL
    rgb_pls = gen_random_pts_around_origin(seed=seed_rgb_pl, N=args.num_rgb_pls, min_dist_to_origin=4.0, max_dist_to_origin=5.0, min_theta_in_degree=0, max_theta_in_degree=60)
    for idx in range(args.num_rgb_pls):
        if is_folder_populated(f'{res_dir}/train/rgb_pl_{idx}', len(cameras)): continue
        pl = rgb_pls[idx]
        power = random.uniform(900, 1500)
        rgb = [random.uniform(0, 1) for _ in range(3)]
        create_point_light(pl, power, rgb=rgb)
        render_views('train', f'rgb_pl_{idx}', cameras)
        render_views('test', f'rgb_pl_{idx}', cameras_test)
        json.dump({'pos': array2list(pl), 'power': power, 'color': rgb}, open(f'{res_dir}/train/rgb_pl_{idx}/rgb_pl.json', 'w'), indent=4)

    # 2.4 Multi PL
    multi_pls = gen_random_pts_around_origin(seed=seed_multi_pl, N=args.num_multi_pls * args.max_pl_num, min_dist_to_origin=3.0, max_dist_to_origin=5.0, min_theta_in_degree=0, max_theta_in_degree=85)
    for idx in range(args.num_multi_pls):
        if is_folder_populated(f'{res_dir}/train/multi_pl_{idx}', len(cameras)): continue
        pls = multi_pls[idx * args.max_pl_num: (idx + 1) * args.max_pl_num]
        powers = [random.uniform(500, 1500) for _ in range(args.max_pl_num)]
        colors = []
        for pl_idx in range(args.max_pl_num):
            rgb = [1.0, 1.0, 1.0] if random.random() < 0.5 else [random.uniform(0.4, 1.0) for _ in range(3)]
            colors.append(rgb)
            create_point_light(pls[pl_idx], powers[pl_idx], rgb=rgb, keep_other_lights=pl_idx > 0)
        render_views('train', f'multi_pl_{idx}', cameras)
        render_views('test', f'multi_pl_{idx}', cameras_test)
        json.dump({'pos': mat2list(pls), 'power': powers, 'color': colors}, open(f'{res_dir}/train/multi_pl_{idx}/multi_pl.json', 'w'), indent=4)

    # 2.5 Colored Env
    for idx in range(args.num_env_lights):
        if is_folder_populated(f'{res_dir}/train/env_{idx}', len(cameras)): continue
        env_map = random.choice(env_map_list)
        set_env_light(f'{args.env_map_dir_path}/{env_map}_8k.exr', rotation_euler=[0, 0, random.uniform(-math.pi, math.pi)], strength=1.0)
        render_views('train', f'env_{idx}', cameras)
        render_views('test', f'env_{idx}', cameras_test)
        json.dump({'env_map': env_map, 'rotation_euler': [0,0,0], 'strength': 1.0}, open(f'{res_dir}/train/env_{idx}/env.json', 'w'), indent=4)

    # 2.6 Area Light
    area_light_positions = gen_random_pts_around_origin(seed=seed_area, N=args.num_area_lights, min_dist_to_origin=3.0, max_dist_to_origin=6.0, min_theta_in_degree=0, max_theta_in_degree=85)
    for idx in range(args.num_area_lights):
        if is_folder_populated(f'{res_dir}/train/area_{idx}', len(cameras)): continue
        pos = area_light_positions[idx]
        power = random.uniform(700, 1500)
        size = random.uniform(5., 10.)
        color = [1.0, 1.0, 1.0] if random.random() < 0.75 else [random.uniform(0.4, 1.0) for _ in range(3)]
        create_area_light(pos, power, size, color=color)
        render_views('train', f'area_{idx}', cameras)
        render_views('test', f'area_{idx}', cameras_test)
        json.dump({'pos': array2list(pos), 'power': power, 'size': size, 'color': color}, open(f'{res_dir}/train/area_{idx}/area.json', 'w'), indent=4)

    with open(os.path.join(res_dir, 'done.txt'), 'w') as f:
        f.write('done')

if __name__ == '__main__':
    args: Options = simple_parsing.parse(Options)
    import csv
    index_uid_list = []
    with open(args.csv_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) == 2:
                index_uid_list.append((row[0].strip(), row[1].strip()))
    
    print(f"Loaded {len(index_uid_list)} entries")
    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)
        
    for i in range(args.group_start, args.group_end):
        print(f"Generating scene {i}")
        selected_objects = random.sample(index_uid_list, args.num_objects_per_scene)
        render_core(args, i, selected_objects)
