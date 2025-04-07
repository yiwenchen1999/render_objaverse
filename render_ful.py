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
    three_d_model_path: str = '/home/hieu/.objaverse/hf-objaverse-v1/glbs/000-091/93b01f3ac4e04bc6aab1c1e7404b04b4.glb' # Base path to 3D models
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

    def configure_blender(render_albedo: bool = True,
                          render_depth: bool = True,
                          render_normal: bool = True,
                          ):
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

        scene = bpy.context.scene


        # if render_depth/albedo/normal pass is enabled
        scene.use_nodes = True
        active_view_layer = bpy.context.view_layer
        if not active_view_layer:
            print("View Layer not found.")
            raise Exception("View layer not found, neither depth, albdedo nor normal pass can be enabled")

        nodes = bpy.context.scene.node_tree.nodes
        links = bpy.context.scene.node_tree.links

        # Clear default nodes
        for n in nodes:
            nodes.remove(n)

        # Create input render layer node
        render_layers = nodes.new('CompositorNodeRLayers')

        # scene.cycles.diffuse_bounces = 1
        # scene.cycles.glossy_bounces = 1
        # scene.cycles.transparent_max_bounces = 3
        # scene.cycles.transmission_bounces = 3
        # scene.cycles.samples = 32
        # scene.cycles.use_denoising = True



if __name__ == '__main__':
    args: Options = simple_parsing.parse(Options)
    print("options:", args)
    render_core(args)
