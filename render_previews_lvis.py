#!/usr/bin/env python3
"""
为 filtered_uids_lvis.csv 中的每个对象渲染一张预览图。

从 eyes_traj 中随机选择一个视角，随机选择一个环境贴图，渲染一张图像。
保存到 /projects/vig/Datasets/objaverse/hf-objaverse-v1/rendered_previews/{uid}.png
"""

import json
import math
import os
import random
import sys
from dataclasses import dataclass
from typing import Optional

import imageio
import numpy as np
import simple_parsing

error_list = []


@dataclass
class Options:
    """预览图渲染脚本配置"""
    csv_path: str = './filtered_uids_lvis.csv'  # CSV 文件路径
    dataset_path: str = '/projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/'  # 数据集路径
    env_map_list_json: str = './assets/hdri/polyhaven_hdris.json'  # 环境贴图列表
    env_map_dir_path: str = '/projects/vig/Datasets/objaverse/envmaps/hdris'  # 环境贴图目录
    output_dir: str = '/projects/vig/Datasets/objaverse/hf-objaverse-v1/rendered_previews'  # 输出目录
    seed: Optional[int] = None  # 随机种子
    group_start: int = 0  # 起始索引
    group_end: int = 10  # 结束索引


def render_preview(args: Options, model_path: str, uid: str):
    """为单个模型渲染一张预览图"""
    import bpy

    from bpy_helper.camera import create_camera, look_at_to_c2w
    from bpy_helper.light import set_env_light
    from bpy_helper.material import clear_emission_and_alpha_nodes
    from bpy_helper.random import gen_pt_traj_around_origin
    from bpy_helper.scene import import_3d_model, normalize_scene, reset_scene
    from bpy_helper.utils import stdout_redirected

    def render_single_image(output_path: str):
        """渲染单张图像"""
        # 设置对象名称
        new_object = bpy.context.scene.objects[-1]
        new_object.name = "shape"
        bpy.context.view_layer.objects.active = new_object
        bpy.context.view_layer.update()

        bpy.context.scene.view_layers["ViewLayer"].material_override = None
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.filepath = output_path

        bpy.ops.render.render(write_still=True)
        bpy.context.view_layer.update()

        # 读取并处理图像（修复边缘锯齿）
        img = imageio.v3.imread(output_path) / 255.
        if img.shape[-1] == 4:
            img = img[..., :3] * img[..., 3:]
        imageio.v3.imwrite(output_path, (img * 255).clip(0, 255).astype(np.uint8))

    def configure_blender():
        """配置 Blender 渲染设置"""
        bpy.context.scene.render.resolution_x = 512
        bpy.context.scene.render.resolution_y = 512
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.preferences.addons["cycles"].preferences.get_devices()

        bpy.context.scene.cycles.device = 'GPU'
        bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'

        # 启用透明通道
        bpy.context.scene.render.film_transparent = True
        bpy.context.scene.render.image_settings.color_mode = 'RGBA'

    # 重置场景
    reset_scene()

    # 1. 准备 3D 模型
    with stdout_redirected():
        import_3d_model(model_path)
    normalize_scene(use_bounding_sphere=True)
    clear_emission_and_alpha_nodes()

    # 配置 Blender
    configure_blender()

    # 2. 加载环境贴图列表
    env_map_list = json.load(open(args.env_map_list_json, 'r'))

    # 3. 生成 eyes_traj 轨迹
    eyes_traj = gen_pt_traj_around_origin(
        seed=args.seed,
        N=100,
        min_dist_to_origin=1.0,
        max_dist_to_origin=1.0,
        theta_in_degree=60,
        z_up=True
    )

    # 4. 随机选择一个视角
    eye = random.choice(eyes_traj)
    fov = 30
    radius = (0.5 / math.tanh(fov / 2. * (math.pi / 180.)))
    eye = [x * radius for x in eye]
    c2w = look_at_to_c2w(eye)

    # 5. 随机选择一个环境贴图
    env_map = random.choice(env_map_list)
    env_map_path = f'{args.env_map_dir_path}/{env_map}_8k.exr'
    rotation_euler = [0, 0, random.uniform(-math.pi, math.pi)]
    strength = 1.0
    set_env_light(env_map_path, rotation_euler=rotation_euler, strength=strength)

    # 6. 创建相机并渲染
    camera = create_camera(c2w, fov)
    bpy.context.scene.camera = camera

    # 7. 确保输出目录存在
    os.makedirs(args.output_dir, exist_ok=True)

    # 8. 渲染并保存
    output_path = os.path.join(args.output_dir, f'{uid}.png')
    with stdout_redirected():
        render_single_image(output_path)

    # 清理
    bpy.data.objects.remove(camera, do_unlink=True)

    print(f'已渲染预览图: {output_path}')


if __name__ == '__main__':
    args: Options = simple_parsing.parse(Options)
    print(args)

    # 读取 CSV 文件
    import csv
    index_uid_list = []
    with open(args.csv_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) == 2:
                folder, uid = row
                index_uid_list.append((folder.strip(), uid.strip()))

    print(f"加载了 {len(index_uid_list)} 个条目")

    # 设置随机种子
    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)

    # 确保输出目录存在
    os.makedirs(args.output_dir, exist_ok=True)

    # 处理指定范围的对象
    for i in range(args.group_start, min(args.group_end, len(index_uid_list))):
        folder, uid = index_uid_list[i]
        model_path = os.path.join(args.dataset_path, folder, f'{uid}.glb')

        # 检查模型文件是否存在
        if not os.path.exists(model_path):
            print(f'警告: 模型文件不存在，跳过: {model_path}')
            continue

        # 检查预览图是否已存在
        output_path = os.path.join(args.output_dir, f'{uid}.png')
        if os.path.exists(output_path):
            print(f'预览图已存在，跳过: {uid}')
            continue

        # 检查是否在错误列表中
        if uid in error_list:
            print(f'跳过错误模型: {uid}')
            continue

        print(f'渲染模型 [{i+1}/{min(args.group_end, len(index_uid_list))}]: {uid}')

        try:
            render_preview(args, model_path, uid)
        except Exception as e:
            print(f'渲染失败 {uid}: {e}', file=sys.stderr)
            error_list.append(uid)
            continue

        print(f'渲染进度: {i+1} / {min(args.group_end, len(index_uid_list))}')

