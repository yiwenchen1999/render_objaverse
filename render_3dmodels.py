import json
import math
import os
from dataclasses import dataclass
import random
from typing import Optional

import imageio
import numpy as np
import simple_parsing


@dataclass
class Options:
    """ 3D dataset rendering script """
    three_d_model_path: str = '/home/hieu/.objaverse/hf-objaverse-v1/glbs/000-091/1f75786d2bf047a38f3971d7758aa990.glb' # Base path to 3D models
    env_map_list_json: str = './assets/hdri/polyhaven_hdris.json'  # Path to env map list
    env_map_dir_path: str = './assets/hdri/files'  # Path to env map directory
    white_env_map_dir_path: str = './assets/hdri/file_bw'  # Path to white env map directory
    output_dir: str = './output'  # Output directory
    num_views: int = 2  # Number of views
    num_white_pls: int = 3  # Number of white point lighting
    num_rgb_pls: int = 0  # Number of RGB point lighting
    num_multi_pls: int = 3  # Number of multi point lighting
    max_pl_num: int = 3  # Maximum number of point lights
    num_white_envs: int = 3  # Number of white env lighting
    num_env_lights: int = 3  # Number of env lighting
    num_area_lights: int = 3  # Number of area lights
    seed: Optional[int] = None  # Random seed


def render_core(args: Options):
    import bpy

    from bpy_helper.camera import create_camera, look_at_to_c2w
    from bpy_helper.io import render_depth_map, mat2list, array2list
    from bpy_helper.light import create_point_light, set_env_light, create_area_light
    from bpy_helper.material import create_white_diffuse_material, create_specular_ggx_material, clear_emission_and_alpha_nodes
    from bpy_helper.random import gen_random_pts_around_origin
    from bpy_helper.scene import import_3d_model, normalize_scene, reset_scene
    from bpy_helper.utils import stdout_redirected

    def render_rgb_and_hint(output_path,idx):
        # Get the last added object (assuming the new object is the most recently added one)
        new_object = bpy.context.scene.objects[-1]
        # Set the name for the newly imported object
        new_object.name = "shape"
        bpy.context.view_layer.objects.active = new_object
        bpy.context.view_layer.update()

        bpy.context.scene.view_layers["ViewLayer"].material_override = None
        bpy.context.scene.render.image_settings.file_format = 'PNG'  # set output to png (with tonemapping)
        bpy.context.scene.render.filepath = os.path.join(output_path, 'gt.png')
        
        # if render_depth/albedo/normal pass is enabled
        bpy.context.scene.use_nodes = True
        active_view_layer = bpy.context.view_layer
        if not active_view_layer:
            print("View Layer not found.")
            raise Exception("View layer not found, neither depth, albdedo nor normal pass can be enabled")

        nodes = bpy.context.scene.node_tree.nodes
        links = bpy.context.scene.node_tree.links

        # Clear default nodes
        while nodes:
            nodes.remove(nodes[0])

        # Create input render layer node
        render_layers = nodes.new('CompositorNodeRLayers')

        # if rendering albedo
        active_view_layer.use_pass_diffuse_color = True
        print("Albedo pass enabled")
        # Create albedo output nodes
        alpha_albedo = nodes.new(type="CompositorNodeSetAlpha")
        links.new(render_layers.outputs['DiffCol'], alpha_albedo.inputs['Image'])
        links.new(render_layers.outputs['Alpha'], alpha_albedo.inputs['Alpha'])

        albedo_file_output = nodes.new(type="CompositorNodeOutputFile")
        albedo_file_output.label = 'Albedo Output'
        albedo_file_output.base_path = output_path
        albedo_file_output.file_slots[0].use_node_format = True
        albedo_file_output.format.file_format = "PNG"
        albedo_file_output.format.color_mode = 'RGBA'
        albedo_file_output.format.color_depth = '16'

        # links.new(alpha_albedo.outputs['Image'], albedo_file_output.inputs[0])

        # albedo_file_output.base_path = 'output'
        albedo_file_output.file_slots[0].path = f'/albedo_{idx}'
        links.new(alpha_albedo.outputs['Image'], albedo_file_output.inputs[0])




        # with stdout_redirected():
        bpy.ops.render.render(write_still=True)
        bpy.context.view_layer.update()


        img = imageio.v3.imread(os.path.join(output_path, 'gt.png')) / 255.
        if img.shape[-1] == 4:
            img = img[..., :3] * img[..., 3:]  # fix edge aliasing
        imageio.v3.imwrite(os.path.join(output_path, 'gt.png'), (img * 255).clip(0, 255).astype(np.uint8))


        # img = imageio.v3.imread(os.path.join(output_path, 'albedo0001.png')) / 255.
        # if img.shape[-1] == 4:
        #     img = img[..., :3] * img[..., 3:]  # fix edge aliasing
        # imageio.v3.imwrite(os.path.join(output_path, 'albedo0001.png'), (img * 255).clip(0, 255).astype(np.uint8))

        # color_depth = '16' # Important for albedo and depth


        # # scene.use_nodes = True
        # active_view_layer = bpy.context.view_layer
        # if not active_view_layer:
        #     print("View Layer not found.")
        #     raise Exception("View layer not found, neither depth, albdedo nor normal pass can be enabled")

        # nodes = bpy.context.scene.node_tree.nodes
        # links = bpy.context.scene.node_tree.links
        # render_layers = nodes.new('CompositorNodeRLayers')


        # active_view_layer.use_pass_diffuse_color = True
        # print("Albedo pass enabled")
        # # Create albedo output nodes
        # alpha_albedo = nodes.new(type="CompositorNodeSetAlpha")
        # links.new(render_layers.outputs['DiffCol'], alpha_albedo.inputs['Image'])
        # links.new(render_layers.outputs['Alpha'], alpha_albedo.inputs['Alpha'])

        # albedo_file_output = nodes.new(type="CompositorNodeOutputFile")
        # albedo_file_output.label = 'Albedo Output'
        # albedo_file_output.base_path = '/'
        # albedo_file_output.file_slots[0].use_node_format = True
        # albedo_file_output.format.file_format = "PNG"
        # albedo_file_output.format.color_mode = 'RGBA'
        # albedo_file_output.format.color_depth = color_depth
        # links.new(alpha_albedo.outputs['Image'], albedo_file_output.inputs[0])
        # bpy.ops.render.render(animation=False, write_still=True)

        # img = imageio.v3.imread(f'{output_path}.png') / 255.
        # if img.shape[-1] == 4:
        #     img = img[..., :3] * img[..., 3:]  # fix edge aliasing
        # imageio.v3.imwrite(f'{output_path}_albedo.png', (img * 255).clip(0, 255).astype(np.uint8))



        # # Enable additional passes
        # bpy.context.view_layer.use_pass_normal = True
        # bpy.context.view_layer.use_pass_diffuse_color = True
        # bpy.context.view_layer.use_pass_glossy_color = True
        # bpy.context.view_layer.use_pass_material_index = True

        # # Use compositor to extract maps
        # scene = bpy.context.scene
        # scene.use_nodes = True
        # tree = scene.node_tree
        # tree.nodes.clear()

        # rl = tree.nodes.new(type='CompositorNodeRLayers')
        # print('--------------------------')
        # # print('input_socket:', input_socket)
        # print(('rl.outputs has keys:', rl.outputs.keys()))


        # # Output directory logic
        # def add_output_node(label, path_suffix):
        #     file_output = tree.nodes.new(type='CompositorNodeOutputFile')
        #     file_output.label = label
        #     file_output.base_path = os.path.dirname(output_path)
        #     file_output.file_slots[0].path = f'{os.path.basename(output_path)}_{path_suffix}_'
        #     return file_output

        # def link_pass(output_node, input_socket):
        #     tree.links.new(rl.outputs[input_socket], output_node.inputs[0])

        # for pass_type, pass_name in [
        #     ('diffuse_color', 'DiffCol'),              
        #     # ('glossy_color', 'GlossCol')
        #                             ]:
        #     out_node = add_output_node(pass_name.capitalize(), pass_type)
        #     link_pass(out_node, pass_name)
        # for pass_name in rl.outputs.keys():
        #     if pass_name == 'IndexMA':
        #         continue
        #     out_node = add_output_node(pass_name.capitalize(), pass_name)
        #     link_pass(out_node, pass_name)

        # Render with compositor
        # bpy.ops.render.render(animation=False, write_still=True)

        # # Re-disable unused passes
        # bpy.context.view_layer.use_pass_normal = False
        # bpy.context.view_layer.use_pass_diffuse_color = False
        # bpy.context.view_layer.use_pass_glossy_color = False
        # bpy.context.view_layer.use_pass_material_index = False

        # MAT_DICT = {
        #     '_diffuse': create_white_diffuse_material(),
        #     '_ggx0.05': create_specular_ggx_material(0.05),
        #     '_ggx0.13': create_specular_ggx_material(0.13),
        #     '_ggx0.34': create_specular_ggx_material(0.34),
        # }

        # # render
        # for mat_name, mat in MAT_DICT.items():
        #     bpy.context.scene.view_layers["ViewLayer"].material_override = mat
        #     bpy.context.scene.render.filepath = f'{output_path}{mat_name}.png'
        #     bpy.ops.render.render(animation=False, write_still=True)
        #     img = imageio.v3.imread(f'{output_path}{mat_name}.png') / 255.
        #     if img.shape[-1] == 4:
        #         img = img[..., :3] * img[..., 3:]  # fix edge aliasing
        #     imageio.v3.imwrite(f'{output_path}{mat_name}.png', (img * 255).clip(0, 255).astype(np.uint8))

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

        # scene = bpy.context.scene
        # scene.cycles.diffuse_bounces = 1
        # scene.cycles.glossy_bounces = 1
        # scene.cycles.transparent_max_bounces = 3
        # scene.cycles.transmission_bounces = 3
        # scene.cycles.samples = 32
        # scene.cycles.use_denoising = True


        # # if render_depth/albedo/normal pass is enabled
        # scene.use_nodes = True
        # active_view_layer = bpy.context.view_layer
        # if not active_view_layer:
        #     print("View Layer not found.")
        #     raise Exception("View layer not found, neither depth, albdedo nor normal pass can be enabled")

        # nodes = bpy.context.scene.node_tree.nodes
        # links = bpy.context.scene.node_tree.links

        # # Clear default nodes
        # for n in nodes:
        #     nodes.remove(n)

        # # Create input render layer node
        # render_layers = nodes.new('CompositorNodeRLayers')

        # # if rendering albedo
        # active_view_layer.use_pass_diffuse_color = True
        # print("Albedo pass enabled")
        # # Create albedo output nodes
        # alpha_albedo = nodes.new(type="CompositorNodeSetAlpha")
        # links.new(render_layers.outputs['DiffCol'], alpha_albedo.inputs['Image'])
        # links.new(render_layers.outputs['Alpha'], alpha_albedo.inputs['Alpha'])

        # albedo_file_output = nodes.new(type="CompositorNodeOutputFile")
        # albedo_file_output.label = 'Albedo Output'
        # albedo_file_output.base_path = '/'
        # albedo_file_output.file_slots[0].use_node_format = True
        # albedo_file_output.format.file_format = "PNG"
        # albedo_file_output.format.color_mode = 'RGBA'
        # albedo_file_output.format.color_depth = '16'
        # links.new(alpha_albedo.outputs['Image'], albedo_file_output.inputs[0])



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
    json.dump({'scale': scale, 'offset': array2list(offset)}, open(f'{res_dir}/normalize.json', 'w'), indent=4)

    eyes = gen_random_pts_around_origin(
        seed=seed_view,
        N=args.num_views,
        min_dist_to_origin=1.0,
        max_dist_to_origin=1.0,
        min_theta_in_degree=10,
        max_theta_in_degree=90
    )
    for eye_idx in range(args.num_views):
        # 0. Place Camera, render gt depth map
        eye = eyes[eye_idx]
        fov = random.uniform(25, 35)
        radius = random.uniform(0.8, 1.1) * (0.5 / math.tanh(fov / 2. * (math.pi / 180.)))
        eye = [x * radius for x in eye]
        c2w = look_at_to_c2w(eye)
        camera = create_camera(c2w, fov)
        bpy.context.scene.camera = camera
        view_path = f'{res_dir}/view_{eye_idx}'
        os.makedirs(view_path, exist_ok=True)
        with stdout_redirected():
            render_depth_map(view_path)
        # save cam info
        json.dump({'c2w': mat2list(c2w), 'fov': fov}, open(f'{view_path}/cam.json', 'w'), indent=4)

        # 1. Single white point light
        white_pls = gen_random_pts_around_origin(
            seed=seed_white_pl,
            N=args.num_white_pls,
            min_dist_to_origin=4.0,
            max_dist_to_origin=5.0,
            min_theta_in_degree=0,
            max_theta_in_degree=60
        )
        for white_pl_idx in range(args.num_white_pls):
            pl = white_pls[white_pl_idx]
            power = random.uniform(500, 1500)
            _point_light = create_point_light(pl, power)
            ref_pl_path = f'{view_path}/white_pl_{white_pl_idx}'
            os.makedirs(ref_pl_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{ref_pl_path}',white_pl_idx)
            # save point light info
            json.dump({
                'pos': array2list(pl),
                'power': power,
            }, open(f'{ref_pl_path}/white_pl.json', 'w'), indent=4)


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
            _point_light = create_point_light(pl, power, rgb=rgb)
            ref_pl_path = f'{view_path}/rgb_pl_{rgb_pl_idx}'
            os.makedirs(ref_pl_path, exist_ok=True)
            with stdout_redirected():
                render_rgb_and_hint(f'{ref_pl_path}')
            # save point light info
            json.dump({
                'pos': array2list(pl),
                'power': power,
                'color': rgb,
            }, open(f'{ref_pl_path}/rgb_pl.json', 'w'), indent=4)


if __name__ == '__main__':
    args: Options = simple_parsing.parse(Options)
    print("options:", args)
    render_core(args)
