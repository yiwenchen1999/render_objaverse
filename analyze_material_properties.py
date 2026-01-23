#!/usr/bin/env python3
"""
分析 GLB 模型文件的材质属性（metallic 和 roughness）并绘制分布图
"""
import os
import csv
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Tuple, Optional
import pygltflib

def find_glb_file(dataset_path: str, index: str, uid: str) -> Optional[str]:
    """
    根据 index 和 uid 查找 GLB 文件路径
    参考 render_3dmodels_dense.py 中的逻辑
    """
    model_path = os.path.join(dataset_path, index, f'{uid}.glb')
    if os.path.exists(model_path):
        return model_path
    return None

def extract_material_properties(glb_path: str) -> List[Tuple[float, float]]:
    """
    从 GLB 文件中提取 metallic 和 roughness 属性
    
    返回: List of (metallic, roughness) tuples
    """
    properties = []
    
    try:
        gltf = pygltflib.GLTF2.load(glb_path)
        
        # 遍历所有材质
        if gltf.materials and len(gltf.materials) > 0:
            for material in gltf.materials:
                metallic = 0.0  # 默认值
                roughness = 1.0  # 默认值
                
                # 检查 PBR 材质属性
                if hasattr(material, 'pbrMetallicRoughness') and material.pbrMetallicRoughness:
                    pbr = material.pbrMetallicRoughness
                    
                    # 获取 metallic 值
                    if hasattr(pbr, 'metallicFactor') and pbr.metallicFactor is not None:
                        try:
                            metallic = float(pbr.metallicFactor)
                            # 确保值在有效范围内 [0, 1]
                            metallic = max(0.0, min(1.0, metallic))
                        except (ValueError, TypeError):
                            metallic = 0.0
                    
                    # 获取 roughness 值
                    if hasattr(pbr, 'roughnessFactor') and pbr.roughnessFactor is not None:
                        try:
                            roughness = float(pbr.roughnessFactor)
                            # 确保值在有效范围内 [0, 1]
                            roughness = max(0.0, min(1.0, roughness))
                        except (ValueError, TypeError):
                            roughness = 1.0
                    
                    properties.append((metallic, roughness))
                else:
                    # 如果没有 PBR 属性，使用默认值
                    properties.append((metallic, roughness))
        else:
            # 如果没有材质，返回一个默认值（表示该模型没有材质信息）
            properties.append((0.0, 1.0))
            
    except Exception as e:
        print(f"处理文件 {glb_path} 时出错: {e}")
        return []
    
    return properties

def analyze_materials_from_csv(csv_path: str, dataset_path: str) -> Tuple[List[float], List[float]]:
    """
    从 CSV 文件中读取模型列表，提取所有材质的 metallic 和 roughness 值
    
    返回: (metallic_values, roughness_values)
    """
    metallic_values = []
    roughness_values = []
    
    index_uid_list = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) == 2:
                index, uid = row
                index_uid_list.append((index.strip(), uid.strip()))
    
    print(f"从 CSV 加载了 {len(index_uid_list)} 个模型")
    
    processed = 0
    failed = 0
    
    for idx, (index, uid) in enumerate(index_uid_list):
        glb_path = find_glb_file(dataset_path, index, uid)
        
        if glb_path is None:
            print(f"[{idx+1}/{len(index_uid_list)}] 未找到文件: {index}/{uid}.glb")
            failed += 1
            continue
        
        if (idx + 1) % 100 == 0:
            print(f"处理进度: {idx+1}/{len(index_uid_list)} (成功: {processed}, 失败: {failed})")
        
        properties = extract_material_properties(glb_path)
        
        if properties:
            for metallic, roughness in properties:
                metallic_values.append(metallic)
                roughness_values.append(roughness)
            processed += 1
        else:
            failed += 1
    
    print(f"\n处理完成: 成功 {processed} 个模型, 失败 {failed} 个模型")
    print(f"总共提取了 {len(metallic_values)} 个材质属性")
    
    return metallic_values, roughness_values

def plot_distributions(metallic_values: List[float], roughness_values: List[float], output_dir: str = "./output"):
    """
    绘制 metallic 和 roughness 的分布图
    """
    os.makedirs(output_dir, exist_ok=True)
    
    metallic_values = np.array(metallic_values)
    roughness_values = np.array(roughness_values)
    
    # 创建图表
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('材质属性分布分析', fontsize=16, fontweight='bold')
    
    # 1. Metallic 直方图
    axes[0, 0].hist(metallic_values, bins=50, edgecolor='black', alpha=0.7, color='skyblue')
    axes[0, 0].set_xlabel('Metallic 值', fontsize=12)
    axes[0, 0].set_ylabel('频数', fontsize=12)
    axes[0, 0].set_title(f'Metallic 分布 (均值: {metallic_values.mean():.3f}, 中位数: {np.median(metallic_values):.3f})', fontsize=12)
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Roughness 直方图
    axes[0, 1].hist(roughness_values, bins=50, edgecolor='black', alpha=0.7, color='lightcoral')
    axes[0, 1].set_xlabel('Roughness 值', fontsize=12)
    axes[0, 1].set_ylabel('频数', fontsize=12)
    axes[0, 1].set_title(f'Roughness 分布 (均值: {roughness_values.mean():.3f}, 中位数: {np.median(roughness_values):.3f})', fontsize=12)
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Metallic vs Roughness 散点图
    axes[1, 0].scatter(metallic_values, roughness_values, alpha=0.3, s=10, color='purple')
    axes[1, 0].set_xlabel('Metallic 值', fontsize=12)
    axes[1, 0].set_ylabel('Roughness 值', fontsize=12)
    axes[1, 0].set_title('Metallic vs Roughness 散点图', fontsize=12)
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. 2D 直方图（热力图）
    hist, xedges, yedges = np.histogram2d(metallic_values, roughness_values, bins=30)
    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
    im = axes[1, 1].imshow(hist.T, origin='lower', extent=extent, aspect='auto', cmap='hot', interpolation='nearest')
    axes[1, 1].set_xlabel('Metallic 值', fontsize=12)
    axes[1, 1].set_ylabel('Roughness 值', fontsize=12)
    axes[1, 1].set_title('Metallic vs Roughness 2D 分布', fontsize=12)
    plt.colorbar(im, ax=axes[1, 1], label='频数')
    
    plt.tight_layout()
    
    # 保存图表
    output_path = os.path.join(output_dir, 'material_properties_distribution.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n图表已保存到: {output_path}")
    
    # 保存统计信息
    stats = {
        'total_materials': len(metallic_values),
        'metallic': {
            'mean': float(metallic_values.mean()),
            'median': float(np.median(metallic_values)),
            'std': float(metallic_values.std()),
            'min': float(metallic_values.min()),
            'max': float(metallic_values.max()),
            'percentiles': {
                '25': float(np.percentile(metallic_values, 25)),
                '50': float(np.percentile(metallic_values, 50)),
                '75': float(np.percentile(metallic_values, 75)),
                '90': float(np.percentile(metallic_values, 90)),
                '95': float(np.percentile(metallic_values, 95)),
            }
        },
        'roughness': {
            'mean': float(roughness_values.mean()),
            'median': float(np.median(roughness_values)),
            'std': float(roughness_values.std()),
            'min': float(roughness_values.min()),
            'max': float(roughness_values.max()),
            'percentiles': {
                '25': float(np.percentile(roughness_values, 25)),
                '50': float(np.percentile(roughness_values, 50)),
                '75': float(np.percentile(roughness_values, 75)),
                '90': float(np.percentile(roughness_values, 90)),
                '95': float(np.percentile(roughness_values, 95)),
            }
        }
    }
    
    stats_path = os.path.join(output_dir, 'material_properties_stats.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"统计信息已保存到: {stats_path}")
    
    # 打印统计摘要
    print("\n" + "="*60)
    print("统计摘要")
    print("="*60)
    print(f"总材质数量: {len(metallic_values)}")
    print(f"\nMetallic:")
    print(f"  均值: {stats['metallic']['mean']:.4f}")
    print(f"  中位数: {stats['metallic']['median']:.4f}")
    print(f"  标准差: {stats['metallic']['std']:.4f}")
    print(f"  范围: [{stats['metallic']['min']:.4f}, {stats['metallic']['max']:.4f}]")
    print(f"\nRoughness:")
    print(f"  均值: {stats['roughness']['mean']:.4f}")
    print(f"  中位数: {stats['roughness']['median']:.4f}")
    print(f"  标准差: {stats['roughness']['std']:.4f}")
    print(f"  范围: [{stats['roughness']['min']:.4f}, {stats['roughness']['max']:.4f}]")
    print("="*60)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='分析 GLB 模型文件的材质属性')
    parser.add_argument('--csv_path', type=str, default='test_obj.csv',
                        help='CSV 文件路径 (默认: test_obj.csv)')
    parser.add_argument('--dataset_path', type=str, 
                        default='/projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/',
                        help='数据集根目录路径 (默认: /projects/vig/Datasets/objaverse/hf-objaverse-v1/glbs/)')
    parser.add_argument('--output_dir', type=str, default='./output',
                        help='输出目录 (默认: ./output)')
    
    args = parser.parse_args()
    
    print("开始分析材质属性...")
    print(f"CSV 文件: {args.csv_path}")
    print(f"数据集路径: {args.dataset_path}")
    print(f"输出目录: {args.output_dir}")
    print("-" * 60)
    
    # 提取材质属性
    metallic_values, roughness_values = analyze_materials_from_csv(
        args.csv_path, 
        args.dataset_path
    )
    
    if len(metallic_values) == 0:
        print("错误: 未能提取到任何材质属性，请检查文件路径和格式")
        return
    
    # 绘制分布图
    plot_distributions(metallic_values, roughness_values, args.output_dir)
    
    print("\n分析完成！")

if __name__ == '__main__':
    main()

