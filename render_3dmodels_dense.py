import json
import math
import os
from dataclasses import dataclass
import random
from typing import Optional
import sys

import imageio
import numpy as np
import simple_parsing
import shutil
error_list = []

@dataclass
class Options:
    """ 3D dataset rendering script """
    three_d_model_path: str = '/projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/000-091/c0a1e0cd1c744f55b5c7df7e8f43eba9.glb' # Base path to 3D models
    env_map_list_json: str = './assets/hdri/polyhaven_hdris.json'  # Path to env map list
    env_map_dir_path: str = '/projects/vig/Datasets/objaverse/envmaps/hdris'  # Path to env map directory
    white_env_map_dir_path: str = '/projects/vig/Datasets/objaverse/envmaps/hdris'  # Path to white env map directory
    output_dir: str = './output'  # Output directory
    num_views: int = 200  # Number of views
    num_white_pls: int = 0  # Number of white point lighting
    num_rgb_pls: int = 0  # Number of RGB point lighting
    num_multi_pls: int = 0  # Number of multi point lighting
    max_pl_num: int = 3  # Maximum number of point lights
    num_white_envs: int = 1  # Number of white env lighting
    num_env_lights: int = 5  # Number of env lighting
    num_area_lights: int = 0  # Number of area lights
    seed: Optional[int] = None  # Random seed
    num_view_groups: int = 1  # Number of view groups
    group_start: int = 0
    group_end: int = 10  # Group of models to render
    save_intrinsics: bool = True  # Whether to save intrinsics for each view


def render_core(args: Options, groups_id = 0):
    import bpy

    from bpy_helper.camera import create_camera, look_at_to_c2w
    from bpy_helper.io import render_depth_map, mat2list, array2list, render_normal_map, render_albedo_map, transform_normals_to_camera_space
    from bpy_helper.light import create_point_light, set_env_light, create_area_light
    from bpy_helper.material import create_white_diffuse_material, create_specular_ggx_material, clear_emission_and_alpha_nodes
    from bpy_helper.random import gen_random_pts_around_origin, gen_pt_traj_around_origin
    from bpy_helper.scene import import_3d_model, normalize_scene, reset_scene
    from bpy_helper.utils import stdout_redirected

    def render_rgb_and_hint(output_path,idx = 0):
        # Get the last added object (assuming the new object is the most recently added one)
        new_object = bpy.context.scene.objects[-1]
        # Set the name for the newly imported object
        new_object.name = "shape"
        bpy.context.view_layer.objects.active = new_object
        bpy.context.view_layer.update()

        bpy.context.scene.view_layers["ViewLayer"].material_override = None
        bpy.context.scene.render.image_settings.file_format = 'PNG'  # set output to png (with tonemapping)
        bpy.context.scene.render.filepath = os.path.join(output_path, f'gt_{idx}.png')
        
        # with stdout_redirected():
        bpy.ops.render.render(write_still=True)
        bpy.context.view_layer.update()

        img = imageio.v3.imread(os.path.join(output_path, f'gt_{idx}.png')) / 255.
        if img.shape[-1] == 4:
            img = img[..., :3] * img[..., 3:]  # fix edge aliasing
        imageio.v3.imwrite(os.path.join(output_path, 'gt_{idx}.png'), (img * 255).clip(0, 255).astype(np.uint8))

    def configure_blender():
        # Set the render resolution
        bpy.context.scene.render.resolution_x = 512
        bpy.context.scene.render.resolution_y = 512
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.preferences.addons["cycles"].preferences.get_devices()

        bpy.context.scene.cycles.device = 'GPU'
        bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'

        # Enable the alpha channel for GT mask
        bpy.context.scene.render.film_transparent = True
        bpy.context.scene.render.image_settings.color_mode = 'RGBA'

    reset_scene()

    #& 1.preparing the scene
    #* 1.1 prepare the 3d model
    file_path = args.three_d_model_path
    with stdout_redirected():
        import_3d_model(file_path)
    scale, offset = normalize_scene(use_bounding_sphere=True)
    clear_emission_and_alpha_nodes()

    # Configure blender
    configure_blender()

    # Load env map list
    env_map_list = json.load(open(args.env_map_list_json, 'r'))

    # Render GT images & hints
    seed_view = None if args.seed is None else args.seed
    seed_white_pl = None if args.seed is None else args.seed + 1
    seed_rgb_pl = None if args.seed is None else args.seed + 2
    seed_multi_pl = None if args.seed is None else args.seed + 3
    seed_area = None if args.seed is None else args.seed + 4
    res_dir = f"{args.output_dir}/{file_path.split('/')[-1].split('.')[0]}"
    os.makedirs(res_dir, exist_ok=True)
    res_dir = os.path.join(res_dir)
    if not os.path.exists(res_dir):
        os.makedirs(res_dir)

    json.dump({'scale': scale, 'offset': array2list(offset)}, open(f'{res_dir}/normalize.json', 'w'), indent=4)

    #* 1.2 prepare the cameras
    eyes = gen_random_pts_around_origin(
        seed=seed_view,
        N=args.num_views,                # set to a large value (e.g. 100, 200, 400)
        min_dist_to_origin=0.8,
        max_dist_to_origin=1.3,          # usually keep min=max for consistent radius
        min_theta_in_degree=0,           # 0 for full sphere, 10/20 for hemisphere
        max_theta_in_degree=100,         # 90 or 70 for upper hemisphere only
        z_up=True
    )
    eyes_traj = gen_pt_traj_around_origin(
        seed=seed_view,
        N=100,
        min_dist_to_origin=1.0,
        max_dist_to_origin=1.0,
        theta_in_degree=60,
        z_up=True
    )
    
    cameras = []
    cameras_test = []
    for eye_idx, eye in enumerate(eyes):
        fov = 30
        radius = (0.5 / math.tanh(fov / 2. * (math.pi / 180.)))
        eye = [x * radius for x in eye]
        c2w = look_at_to_c2w(eye)
        cameras.append((eye_idx, c2w, fov))

    for eye_idx, eye in enumerate(eyes_traj):
        fov = 30
        radius = (0.5 / math.tanh(fov / 2. * (math.pi / 180.)))
        eye = [x * radius for x in eye]
        c2w = look_at_to_c2w(eye)
        cameras_test.append((eye_idx, c2w, fov))
    
    #& 2. start rendering
    intrinsics_saved = not args.save_intrinsics
    
    #* 2.1 render the white env lighting first
    for env_idx in range(args.num_white_envs):
        # Use the white environment map we created
        env_map_path = f'{args.white_env_map_dir_path}/white_env_8k.exr'
        rotation_euler = [0, 0, random.uniform(-math.pi, math.pi)]
        strength = 1.0
        set_env_light(env_map_path, rotation_euler=rotation_euler, strength=strength)

        all_cams = []  # <-- Collect all cams for this env

        for eye_idx, c2w, fov in cameras:
            camera = create_camera(c2w, fov)
            bpy.context.scene.camera = camera
            view_path = f'{res_dir}/train'
            if not os.path.exists(view_path):
                os.makedirs(view_path)

            if not intrinsics_saved:
                with stdout_redirected():
                    render_depth_map(view_path, file_prefix=f'depth_{eye_idx}')
                    render_normal_map(view_path)
                    render_albedo_map(view_path)
                # copy the depth map to a different name
                depth_folder = os.path.join(view_path, 'depth')
                os.makedirs(depth_folder, exist_ok=True)
                depth_path = os.path.join(view_path, f'depth_{eye_idx}0001.exr')
                depth_cam_path = os.path.join(depth_folder, f'depth_{eye_idx}.exr')
                shutil.copy(depth_path, depth_cam_path)
                # Transform normals to camera space
                normals_path = os.path.join(view_path, 'normal0001.exr')
                normal_folder = os.path.join(view_path, 'normal')
                os.makedirs(normal_folder, exist_ok=True)
                normals_cam_path = os.path.join(normal_folder, f'normal_cam_{eye_idx}.exr')
                transform_normals_to_camera_space(normals_path, c2w, normals_cam_path)
                albedo_path = os.path.join(view_path, 'albedo0001.png')
                albedo_folder = os.path.join(view_path, 'albedo')
                os.makedirs(albedo_folder, exist_ok=True)
                albedo_cam_path = os.path.join(albedo_folder, f'albedo_cam_{eye_idx}.png')
                shutil.copy(albedo_path, albedo_cam_path)
                # clean up the files before they got moved:
                os.remove(os.path.join(view_path, f'depth_{eye_idx}0001.exr'))
                os.remove(os.path.join(view_path, 'normal0001.exr'))
                os.remove(os.path.join(view_path, 'albedo0001.png'))
                # remove ant files with "rgb_for_" prefix
                for file in os.listdir(view_path):
                    if file.startswith('rgb_for_'):
                        os.remove(os.path.join(view_path, file))

            # Instead of saving cam.json per view, collect the info:
            cam_entry = {
                'eye_idx': eye_idx,
                'c2w': mat2list(c2w),
                'fov': fov,
            }
            all_cams.append(cam_entry)

            env_path = f'{view_path}/white_env_{env_idx}'
            os.makedirs(env_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{env_path}', eye_idx)

            bpy.data.objects.remove(camera, do_unlink=True)

        # === Save all camera info for this env in a single file ===
        cameras_json_path = os.path.join(view_path, f'cameras.json')
        json.dump(all_cams, open(cameras_json_path, 'w'), indent=4)

        #* render the test views for white env lighting
        for eye_idx, c2w, fov in cameras_test:
            camera = create_camera(c2w, fov)
            bpy.context.scene.camera = camera
            view_path = f'{res_dir}/test'
            if not os.path.exists(view_path):
                os.makedirs(view_path)

            if not intrinsics_saved:
                with stdout_redirected():
                    render_depth_map(view_path, file_prefix=f'depth_{eye_idx}')
                    render_normal_map(view_path)
                    render_albedo_map(view_path)
                # copy the depth map to a different name
                depth_folder = os.path.join(view_path, 'depth')
                os.makedirs(depth_folder, exist_ok=True)
                depth_path = os.path.join(view_path, f'depth_{eye_idx}0001.exr')
                depth_cam_path = os.path.join(depth_folder, f'depth_{eye_idx}.exr')
                shutil.copy(depth_path, depth_cam_path)
                # Transform normals to camera space
                normals_path = os.path.join(view_path, 'normal0001.exr')
                normal_folder = os.path.join(view_path, 'normal')
                os.makedirs(normal_folder, exist_ok=True)
                normals_cam_path = os.path.join(normal_folder, f'normal_cam_{eye_idx}.exr')
                transform_normals_to_camera_space(normals_path, c2w, normals_cam_path)
                albedo_path = os.path.join(view_path, 'albedo0001.png')
                albedo_folder = os.path.join(view_path, 'albedo')
                os.makedirs(albedo_folder, exist_ok=True)
                albedo_cam_path = os.path.join(albedo_folder, f'albedo_cam_{eye_idx}.png')
                shutil.copy(albedo_path, albedo_cam_path)
                # clean up the files before they got moved:
                os.remove(os.path.join(view_path, f'depth_{eye_idx}0001.exr'))
                os.remove(os.path.join(view_path, 'normal0001.exr'))
                os.remove(os.path.join(view_path, 'albedo0001.png'))
                # remove ant files with "rgb_for_" prefix
                for file in os.listdir(view_path):
                    if file.startswith('rgb_for_'):
                        os.remove(os.path.join(view_path, file))

            # Instead of saving cam.json per view, collect the info:
            cam_entry = {
                'eye_idx': eye_idx,
                'c2w': mat2list(c2w),
                'fov': fov,
            }
            all_cams.append(cam_entry)

            env_path = f'{view_path}/white_env_{env_idx}'
            os.makedirs(env_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{env_path}', eye_idx)

            bpy.data.objects.remove(camera, do_unlink=True)
            
        # === Save all camera info for this env in a single file ===
        cameras_json_path = os.path.join(view_path, f'cameras.json')
        json.dump(all_cams, open(cameras_json_path, 'w'), indent=4)

        # save the env map
        json.dump({
            'env_map': 'white_env_8k.exr',
            'rotation_euler': rotation_euler,
            'strength': strength,
            }, open(f'{env_path}/white_env.json', 'w'), indent=4)

        intrinsics_saved = True

    #* 2.2 render the white point lighting
    white_pls = gen_random_pts_around_origin(
        seed=seed_white_pl,
        N=args.num_white_pls,
        min_dist_to_origin=3.5,
        max_dist_to_origin=5.0,
        min_theta_in_degree=0,
        max_theta_in_degree=85
    )
    for white_pl_idx in range(args.num_white_pls):
        pl = white_pls[white_pl_idx]
        power = random.uniform(500, 1500)
        _point_light = create_point_light(pl, power)
        
        for eye_idx, c2w, fov in cameras:
            camera = create_camera(c2w, fov)
            bpy.context.scene.camera = camera
            view_path = f'{res_dir}/train'
            if not os.path.exists(view_path):
                os.makedirs(view_path)

            env_path = f'{view_path}/white_pl_{white_pl_idx}'
            os.makedirs(env_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{env_path}', eye_idx)

            bpy.data.objects.remove(camera, do_unlink=True)

        #* render the test views for white point lighting
        for eye_idx, c2w, fov in cameras_test:
            camera = create_camera(c2w, fov)
            bpy.context.scene.camera = camera
            view_path = f'{res_dir}/test'
            if not os.path.exists(view_path):
                os.makedirs(view_path)

            env_path = f'{view_path}/white_pl_{white_pl_idx}'
            os.makedirs(env_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{env_path}', eye_idx)

            bpy.data.objects.remove(camera, do_unlink=True)

        # save the point light info
        json.dump({
            'pos': array2list(pl),
            'power': power,
        }, open(f'{env_path}/white_pl.json', 'w'), indent=4)

    #* 2.3 render the RGB point lighting
    rgb_pls = gen_random_pts_around_origin(
        seed=seed_rgb_pl,
        N=args.num_rgb_pls,
        min_dist_to_origin=4.0,
        max_dist_to_origin=5.0,
        min_theta_in_degree=0,
        max_theta_in_degree=60
    )
    for rgb_pl_idx in range(args.num_rgb_pls):
        pl = rgb_pls[rgb_pl_idx]
        power = random.uniform(900, 1500)  # slightly brighter than white light
        rgb = [random.uniform(0, 1) for _ in range(3)]
        create_point_light(pl, power, rgb=rgb)

        for eye_idx, c2w, fov in cameras:
            camera = create_camera(c2w, fov)
            bpy.context.scene.camera = camera
            view_path = f'{res_dir}/train'
            if not os.path.exists(view_path):
                os.makedirs(view_path)

            env_path = f'{view_path}/rgb_pl_{rgb_pl_idx}'
            os.makedirs(env_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{env_path}', eye_idx)

            bpy.data.objects.remove(camera, do_unlink=True)

        #* render the test views for RGB point lighting
        for eye_idx, c2w, fov in cameras_test:
            camera = create_camera(c2w, fov)
            bpy.context.scene.camera = camera
            view_path = f'{res_dir}/test'
            if not os.path.exists(view_path):
                os.makedirs(view_path)

            env_path = f'{view_path}/rgb_pl_{rgb_pl_idx}'
            os.makedirs(env_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{env_path}', eye_idx)

            bpy.data.objects.remove(camera, do_unlink=True)

        # save the RGB point light info
        json.dump({
            'pos': array2list(pl),
            'power': power,
            'color': rgb,
        }, open(f'{env_path}/rgb_pl.json', 'w'), indent=4)

    #* 2.4 render the multi point lighting
    multi_pls = gen_random_pts_around_origin(
        seed=seed_multi_pl,
        N=args.num_multi_pls * args.max_pl_num,
        min_dist_to_origin=3.0,
        max_dist_to_origin=5.0,
        min_theta_in_degree=0,
        max_theta_in_degree=85
    )

    for multi_pl_idx in range(args.num_multi_pls):
        pls = multi_pls[multi_pl_idx * args.max_pl_num: (multi_pl_idx + 1) * args.max_pl_num]
        powers = [random.uniform(500, 1500) for _ in range(args.max_pl_num)]
        colors = []
        for pl_idx in range(args.max_pl_num):
            if random.random() < 0.5:
                rgb = [1.0, 1.0, 1.0]  # white
            else:
                rgb = [random.uniform(0.4, 1.0) for _ in range(3)]  # colored
            colors.append(rgb)
            create_point_light(pls[pl_idx], powers[pl_idx], rgb=rgb, keep_other_lights=pl_idx > 0)

        for eye_idx, c2w, fov in cameras:
            camera = create_camera(c2w, fov)
            bpy.context.scene.camera = camera
            view_path = f'{res_dir}/train'
            if not os.path.exists(view_path):
                os.makedirs(view_path)

            env_path = f'{view_path}/multi_pl_{multi_pl_idx}'
            os.makedirs(env_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{env_path}', eye_idx)

            bpy.data.objects.remove(camera, do_unlink=True)

        #* render the test views for multi point lighting
        for eye_idx, c2w, fov in cameras_test:
            camera = create_camera(c2w, fov)
            bpy.context.scene.camera = camera
            view_path = f'{res_dir}/test'
            if not os.path.exists(view_path):
                os.makedirs(view_path)

            env_path = f'{view_path}/multi_pl_{multi_pl_idx}'
            os.makedirs(env_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{env_path}', eye_idx)

            bpy.data.objects.remove(camera, do_unlink=True)

        # save the multi point light info
        json.dump({
            'pos': mat2list(pls),
            'power': powers,
            'color': colors,
        }, open(f'{env_path}/multi_pl.json', 'w'), indent=4)

    #* 2.5 render the colored env lighting
    for env_map_idx in range(args.num_env_lights):
        env_map = random.choice(env_map_list)
        env_map_path = f'{args.env_map_dir_path}/{env_map}_8k.exr'
        rotation_euler = [0, 0, random.uniform(-math.pi, math.pi)]
        strength = 1.0
        set_env_light(env_map_path, rotation_euler=rotation_euler, strength=strength)

        for eye_idx, c2w, fov in cameras:
            camera = create_camera(c2w, fov)
            bpy.context.scene.camera = camera
            view_path = f'{res_dir}/train'
            if not os.path.exists(view_path):
                os.makedirs(view_path)

            env_path = f'{view_path}/env_{env_map_idx}'
            os.makedirs(env_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{env_path}', eye_idx)

            bpy.data.objects.remove(camera, do_unlink=True)

        #* render the test views for colored env lighting
        for eye_idx, c2w, fov in cameras_test:
            camera = create_camera(c2w, fov)
            bpy.context.scene.camera = camera
            view_path = f'{res_dir}/test'
            if not os.path.exists(view_path):
                os.makedirs(view_path)

            env_path = f'{view_path}/env_{env_map_idx}'
            os.makedirs(env_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{env_path}', eye_idx)

            bpy.data.objects.remove(camera, do_unlink=True)

        # save the env map
        json.dump({
            'env_map': env_map,
            'rotation_euler': rotation_euler,
            'strength': strength,
        }, open(f'{env_path}/env.json', 'w'), indent=4)

    #* 2.6 render the area lighting
    area_light_positions = gen_random_pts_around_origin(
        seed=seed_area,
        N=args.num_area_lights,
        min_dist_to_origin=3.0,
        max_dist_to_origin=6.0,
        min_theta_in_degree=0,
        max_theta_in_degree=85
    )
    for area_light_idx in range(args.num_area_lights):
        area_light_pos = area_light_positions[area_light_idx]
        area_light_power = random.uniform(700, 1500)
        area_light_size = random.uniform(5., 10.)
        if random.random() < 0.75:
            color = [1.0, 1.0, 1.0]  # white
        else:
            color = [random.uniform(0.4, 1.0) for _ in range(3)]  # colored

        _area_light = create_area_light(area_light_pos, area_light_power, area_light_size, color=color)

        for eye_idx, c2w, fov in cameras:
            camera = create_camera(c2w, fov)
            bpy.context.scene.camera = camera
            view_path = f'{res_dir}/train'
            if not os.path.exists(view_path):
                os.makedirs(view_path)

            env_path = f'{view_path}/area_{area_light_idx}'
            os.makedirs(env_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{env_path}', eye_idx)

            bpy.data.objects.remove(camera, do_unlink=True)

        #* render the test views for area lighting
        for eye_idx, c2w, fov in cameras_test:
            camera = create_camera(c2w, fov)
            bpy.context.scene.camera = camera
            view_path = f'{res_dir}/test'
            if not os.path.exists(view_path):
                os.makedirs(view_path)

            env_path = f'{view_path}/area_{area_light_idx}'
            os.makedirs(env_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{env_path}', eye_idx)

            bpy.data.objects.remove(camera, do_unlink=True)

        # save the area light info
        json.dump({
            'pos': array2list(area_light_pos),
            'power': area_light_power,
            'size': area_light_size,
            'color': color,
        }, open(f'{env_path}/area.json', 'w'), indent=4)

    # store a file indicating the end of the rendering
    with open(os.path.join(res_dir, 'done.txt'), 'w') as f:
        f.write('done')
        f.close()


if __name__ == '__main__':
    dataset_path = '/projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/'

    args: Options = simple_parsing.parse(Options)
    print(Options)
    import csv
    csv_path = "test_obj.csv"
    index_uid_list = []
    with open(csv_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) == 2:
                index, uid = row
                index_uid_list.append((index.strip(), uid.strip()))
    # Preview
    print(f"Loaded {len(index_uid_list)} entries")

    for i in range(args.group_start, args.group_end):
        index, uid = index_uid_list[i]
        # index = '000-027'
        # uid = '20b23d4a703e4f7ebfb105b6b140b6fe'
        model_path = os.path.join(dataset_path, index, f'{uid}.glb')
        # model_path = os.path.join(dataset_path,'000-000', f'000074a334c541878360457c672b6c2e.glb')
        args.three_d_model_path = model_path
        if not os.path.exists(dataset_path.replace('glbs','rendered_dense')):
            os.makedirs(dataset_path.replace('glbs','rendered_dense'))
        args.output_dir = os.path.join(dataset_path.replace('glbs','rendered_dense'))
        # Set the seed for reproducibility
        if args.seed is not None:
            random.seed(args.seed)
            np.random.seed(args.seed)
        # Render the model
        print('Rendering model:', uid)
        if uid in error_list:
            print('skipping this model')
            continue
        for j in range(args.num_view_groups):
            # if found a done.txt file, skip this model
            print('rendering group:', j)
            if os.path.exists(os.path.join(args.output_dir, uid, 'done.txt')):
                continue
            render_core(args, j)
            print('render progress:', i, 'of range', args.group_start, '~', args.group_end)
        
