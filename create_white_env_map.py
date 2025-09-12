#!/usr/bin/env python3
"""
Create a white environment map for rendering objects under white environment lighting.
This script generates a pure white EXR environment map that can be used for consistent lighting.
"""

import numpy as np
import OpenEXR
import Imath
import os
import sys

def create_white_env_map(width=8192, height=4096, output_path="white_env_8k.exr"):
    """
    Create a pure white environment map in EXR format.
    
    Args:
        width (int): Width of the environment map (default: 8192 for 8K)
        height (int): Height of the environment map (default: 4096 for 8K)
        output_path (str): Output file path for the EXR file
    """
    
    # Create a pure white image (RGB values all set to 1.0)
    # EXR format typically uses 32-bit float values
    white_image = np.ones((height, width, 3), dtype=np.float32)
    
    # Convert to separate R, G, B channels
    r_channel = white_image[:, :, 0].astype(np.float32)
    g_channel = white_image[:, :, 1].astype(np.float32)
    b_channel = white_image[:, :, 2].astype(np.float32)
    
    # Create EXR header
    header = OpenEXR.Header(width, height)
    header['channels'] = {
        'R': Imath.Channel(Imath.PixelType(Imath.PixelType.FLOAT)),
        'G': Imath.Channel(Imath.PixelType(Imath.PixelType.FLOAT)),
        'B': Imath.Channel(Imath.PixelType(Imath.PixelType.FLOAT))
    }
    
    # Write the EXR file
    exr_file = OpenEXR.OutputFile(output_path, header)
    exr_file.writePixels({
        'R': r_channel.tobytes(),
        'G': g_channel.tobytes(),
        'B': b_channel.tobytes()
    })
    exr_file.close()
    
    print(f"Created white environment map: {output_path}")
    print(f"Dimensions: {width}x{height}")
    print(f"Format: EXR with 32-bit float RGB channels")

def create_white_env_map_simple(width=8192, height=4096, output_path="white_env_8k.exr"):
    """
    Alternative method using imageio for creating white environment map.
    This is simpler but may not preserve all EXR metadata.
    """
    try:
        import imageio
        import imageio.plugins.exr
        
        # Create a pure white image
        white_image = np.ones((height, width, 3), dtype=np.float32)
        
        # Write as EXR
        imageio.imwrite(output_path, white_image, format='EXR')
        
        print(f"Created white environment map: {output_path}")
        print(f"Dimensions: {width}x{height}")
        print(f"Format: EXR with 32-bit float RGB channels")
        
    except ImportError:
        print("imageio not available, falling back to OpenEXR method")
        create_white_env_map(width, height, output_path)

if __name__ == "__main__":
    # Default output path
    output_path = "white_env_8k.exr"
    
    # Check if output path is provided as command line argument
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    
    # Create the white environment map
    try:
        create_white_env_map_simple(output_path=output_path)
    except Exception as e:
        print(f"Error creating white environment map: {e}")
        print("Make sure you have the required dependencies installed:")
        print("pip install OpenEXR imageio")
        sys.exit(1)
