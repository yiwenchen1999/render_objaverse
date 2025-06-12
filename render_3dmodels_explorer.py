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
error_list = []

@dataclass
class Options:
    """ 3D dataset rendering script """
    three_d_model_path: str = '/projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/000-091/c0a1e0cd1c744f55b5c7df7e8f43eba9.glb' # Base path to 3D models
    env_map_list_json: str = './assets/hdri/polyhaven_hdris.json'  # Path to env map list
    env_map_dir_path: str = './assets/hdri/files'  # Path to env map directory
    white_env_map_dir_path: str = './assets/hdri/file_bw'  # Path to white env map directory
    output_dir: str = './output'  # Output directory
    num_views: int = 4  # Number of views
    num_white_pls: int = 2  # Number of white point lighting
    num_rgb_pls: int = 2  # Number of RGB point lighting
    num_multi_pls: int = 2  # Number of multi point lighting
    max_pl_num: int = 3  # Maximum number of point lights
    num_white_envs: int = 0  # Number of white env lighting
    num_env_lights: int = 0  # Number of env lighting
    num_area_lights: int = 2  # Number of area lights
    seed: Optional[int] = None  # Random seed
    num_view_groups: int = 2  # Number of view groups
    group_start: int = 0
    group_end: int = 10  # Group of models to render


def render_core(args: Options, groups_id = 0):
    import bpy

    from bpy_helper.camera import create_camera, look_at_to_c2w
    from bpy_helper.io import render_depth_map, mat2list, array2list, render_normal_map, render_albedo_map, transform_normals_to_camera_space
    from bpy_helper.light import create_point_light, set_env_light, create_area_light
    from bpy_helper.material import create_white_diffuse_material, create_specular_ggx_material, clear_emission_and_alpha_nodes
    from bpy_helper.random import gen_random_pts_around_origin, gen_clustered_pts_around_origin
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
        bpy.context.scene.render.filepath = os.path.join(output_path, 'gt.png')
        
        # with stdout_redirected():
        bpy.ops.render.render(write_still=True)
        bpy.context.view_layer.update()

        img = imageio.v3.imread(os.path.join(output_path, 'gt.png')) / 255.
        if img.shape[-1] == 4:
            img = img[..., :3] * img[..., 3:]  # fix edge aliasing
        imageio.v3.imwrite(os.path.join(output_path, 'gt.png'), (img * 255).clip(0, 255).astype(np.uint8))

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

    # Import the 3D object
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
    res_dir = os.path.join(res_dir, f'group_{groups_id}')
    if not os.path.exists(res_dir):
        os.makedirs(res_dir)

    json.dump({'scale': scale, 'offset': array2list(offset)}, open(f'{res_dir}/normalize.json', 'w'), indent=4)

    eyes = gen_clustered_pts_around_origin(
        seed=seed_view,
        N=args.num_views,
        min_dist_to_origin=1.0,
        max_dist_to_origin=1.0,
        min_theta_in_degree=10,
        max_theta_in_degree=70,
        dist_range=0.1,
        theta_range_deg=22,
        phi_range_deg=60,
    )
    cameras = []
    for eye_idx, eye in enumerate(eyes):
        fov = random.uniform(25, 35)
        radius = random.uniform(0.8, 1.1) * (0.5 / math.tanh(fov / 2. * (math.pi / 180.)))
        eye = [x * radius for x in eye]
        c2w = look_at_to_c2w(eye)
        cameras.append((eye_idx, c2w, fov))

    intrinsics_saved = False
    # 1. Single white point light
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
            # Place Camera, render gt depth map
            camera = create_camera(c2w, fov)
            bpy.context.scene.camera = camera
            view_path = f'{res_dir}/view_{eye_idx}'
            if not os.path.exists(view_path):
                os.makedirs(view_path)

            # save intrinsics property and the current camera info
            if not intrinsics_saved:
                with stdout_redirected():
                    render_depth_map(view_path)
                    render_normal_map(view_path)
                    render_albedo_map(view_path)
                # Transform normals to camera space
                normals_path = os.path.join(view_path, 'normal0001.exr')
                normals_cam_path = os.path.join(view_path, 'normal_cam.exr')
                transform_normals_to_camera_space(normals_path, c2w, normals_cam_path)
                # save cam info
                json.dump({'c2w': mat2list(c2w), 'fov': fov}, open(f'{view_path}/cam.json', 'w'), indent=4)
                
            # render the RGB image for this view and this illu
            ref_pl_path = f'{view_path}/white_pl_{white_pl_idx}'
            os.makedirs(ref_pl_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{ref_pl_path}',white_pl_idx)
            # save point light info
            json.dump({
                'pos': array2list(pl),
                'power': power,
            }, open(f'{ref_pl_path}/white_pl.json', 'w'), indent=4)
            # Clean up this camera after use
            bpy.data.objects.remove(camera, do_unlink=True)
        # need to save the intrinsic for every view
        intrinsics_saved = True
    
    # 2. Single RGB point light
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
            view_path = f'{res_dir}/view_{eye_idx}'
            if not os.path.exists(view_path):
                os.makedirs(view_path)

            # save intrinsics property and the current camera info
            if not intrinsics_saved:
                with stdout_redirected():
                    render_depth_map(view_path)
                    render_normal_map(view_path)
                    render_albedo_map(view_path)
                # Transform normals to camera space
                normals_path = os.path.join(view_path, 'normal0001.exr')
                normals_cam_path = os.path.join(view_path, 'normal_cam.exr')
                transform_normals_to_camera_space(normals_path, c2w, normals_cam_path)
                # save cam info
                json.dump({'c2w': mat2list(c2w), 'fov': fov}, open(f'{view_path}/cam.json', 'w'), indent=4)

            ref_pl_path = f'{view_path}/rgb_pl_{rgb_pl_idx}'
            os.makedirs(ref_pl_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{ref_pl_path}', rgb_pl_idx)

            json.dump({
                'pos': array2list(pl),
                'power': power,
                'color': rgb,
            }, open(f'{ref_pl_path}/rgb_pl.json', 'w'), indent=4)

            bpy.data.objects.remove(camera, do_unlink=True)
        # need to save the intrinsic for every view
        intrinsics_saved = True

    # 3. multi point light
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
            view_path = f'{res_dir}/view_{eye_idx}'
            if not os.path.exists(view_path):
                os.makedirs(view_path)

            # save intrinsics property and the current camera info
            if not intrinsics_saved:
                with stdout_redirected():
                    render_depth_map(view_path)
                    render_normal_map(view_path)
                    render_albedo_map(view_path)
                # Transform normals to camera space
                normals_path = os.path.join(view_path, 'normal0001.exr')
                normals_cam_path = os.path.join(view_path, 'normal_cam.exr')
                transform_normals_to_camera_space(normals_path, c2w, normals_cam_path)
                # save cam info
                json.dump({'c2w': mat2list(c2w), 'fov': fov}, open(f'{view_path}/cam.json', 'w'), indent=4)

            ref_pl_path = f'{view_path}/multi_pl_{multi_pl_idx}'
            os.makedirs(ref_pl_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{ref_pl_path}', multi_pl_idx)

            json.dump({
                'pos': mat2list(pls),
                'power': powers,
                'color': colors,
            }, open(f'{ref_pl_path}/multi_pl.json', 'w'), indent=4)

            bpy.data.objects.remove(camera, do_unlink=True)
        # need to save the intrinsic for every view
        intrinsics_saved = True

    # 4. env lighting white
    for env_idx in range(args.num_white_envs):
        env_map = random.choice(env_map_list)
        env_map_path = f'{args.white_env_map_dir_path}/{env_map}.exr'
        rotation_euler = [0, 0, random.uniform(-math.pi, math.pi)]
        strength = 1.0
        set_env_light(env_map_path, rotation_euler=rotation_euler, strength=strength)

        for eye_idx, c2w, fov in cameras:
            camera = create_camera(c2w, fov)
            bpy.context.scene.camera = camera
            view_path = f'{res_dir}/view_{eye_idx}'
            if not os.path.exists(view_path):
                os.makedirs(view_path)

                if not intrinsics_saved:
                    with stdout_redirected():
                        render_depth_map(view_path)
                        render_normal_map(view_path)
                        render_albedo_map(view_path)
                    # Transform normals to camera space
                    normals_path = os.path.join(view_path, 'normal0001.exr')
                    normals_cam_path = os.path.join(view_path, 'normal_cam.exr')
                    transform_normals_to_camera_space(normals_path, c2w, normals_cam_path)
                    json.dump({'c2w': mat2list(c2w), 'fov': fov}, open(f'{view_path}/cam.json', 'w'), indent=4)

            env_path = f'{view_path}/white_env_{env_idx}'
            os.makedirs(env_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{env_path}', env_idx)

            json.dump({
                'env_map': env_map,
                'rotation_euler': rotation_euler,
                'strength': strength,
            }, open(f'{env_path}/white_env.json', 'w'), indent=4)

            bpy.data.objects.remove(camera, do_unlink=True)
        intrinsics_saved = True

    # 5. env lighting colored
    for env_map_idx in range(args.num_env_lights):
        env_map = random.choice(env_map_list)
        env_map_path = f'{args.env_map_dir_path}/{env_map}.exr'
        rotation_euler = [0, 0, random.uniform(-math.pi, math.pi)]
        strength = 1.0
        set_env_light(env_map_path, rotation_euler=rotation_euler, strength=strength)

        for eye_idx, c2w, fov in cameras:
            camera = create_camera(c2w, fov)
            bpy.context.scene.camera = camera
            view_path = f'{res_dir}/view_{eye_idx}'
            if not os.path.exists(view_path):
                os.makedirs(view_path)

            if not intrinsics_saved:
                with stdout_redirected():
                    render_depth_map(view_path)
                    render_normal_map(view_path)
                    render_albedo_map(view_path)
                # Transform normals to camera space
                normals_path = os.path.join(view_path, 'normal0001.exr')
                normals_cam_path = os.path.join(view_path, 'normal_cam.exr')
                transform_normals_to_camera_space(normals_path, c2w, normals_cam_path)

                json.dump({'c2w': mat2list(c2w), 'fov': fov}, open(f'{view_path}/cam.json', 'w'), indent=4)

            env_path = f'{view_path}/env_{env_map_idx}'
            os.makedirs(env_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{env_path}')

            json.dump({
                'env_map': env_map,
                'rotation_euler': rotation_euler,
                'strength': strength,
            }, open(f'{env_path}/env.json', 'w'), indent=4)

            bpy.data.objects.remove(camera, do_unlink=True)
        intrinsics_saved = True

    # 6. area light
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
            view_path = f'{res_dir}/view_{eye_idx}'
            if not os.path.exists(view_path):
                os.makedirs(view_path)

            if not intrinsics_saved:
                with stdout_redirected():
                    render_depth_map(view_path)
                    render_normal_map(view_path)
                    render_albedo_map(view_path)
                # Transform normals to camera space
                normals_path = os.path.join(view_path, 'normal0001.exr')
                normals_cam_path = os.path.join(view_path, 'normal_cam.exr')
                transform_normals_to_camera_space(normals_path, c2w, normals_cam_path)
                json.dump({'c2w': mat2list(c2w), 'fov': fov}, open(f'{view_path}/cam.json', 'w'), indent=4)

            area_path = f'{view_path}/area_{area_light_idx}'
            os.makedirs(area_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{area_path}')

            json.dump({
                'pos': array2list(area_light_pos),
                'power': area_light_power,
                'size': area_light_size,
                'color': color,
            }, open(f'{area_path}/area.json', 'w'), indent=4)

            bpy.data.objects.remove(camera, do_unlink=True)
        intrinsics_saved = True
    # store a file indicating the end of the rendering
    with open(os.path.join(res_dir, 'done.txt'), 'w') as f:
        f.write('done')
        f.close()


if __name__ == '__main__':
    dataset_path = '/projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/'

    args: Options = simple_parsing.parse(Options)
    print(Options)
    import csv
    csv_path = "../filtered_uids.csv"
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
        model_path = os.path.join(dataset_path,index, f'{uid}.glb')
        args.three_d_model_path = model_path
        if not os.path.exists(dataset_path.replace('glbs','rendered')):
            os.makedirs(dataset_path.replace('glbs','rendered'))
        args.output_dir = os.path.join(dataset_path.replace('glbs','rendered'),index)
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
            if os.path.exists(os.path.join(args.output_dir, uid, 'group_' + str(j), 'done.txt')):
                continue
            render_core(args, j)
            print('render progress:', i, 'of range', args.group_start, '~', args.group_end)
