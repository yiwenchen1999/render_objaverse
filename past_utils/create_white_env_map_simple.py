#!/usr/bin/env python3
"""
Create a white environment map for rendering objects under white environment lighting.
This script generates a pure white EXR environment map using basic Python libraries.
"""

import struct
import os
import sys

def create_white_env_map_exr(width=8192, height=4096, output_path="white_env_8k.exr"):
    """
    Create a pure white environment map in EXR format using basic Python.
    
    Args:
        width (int): Width of the environment map (default: 8192 for 8K)
        height (int): Height of the environment map (default: 4096 for 8K)
        output_path (str): Output file path for the EXR file
    """
    
    # EXR file structure
    # We'll create a minimal EXR file with white pixels
    
    # Calculate total pixels
    total_pixels = width * height
    
    # Create white pixel data (32-bit float, RGB)
    # Each pixel is 3 * 4 bytes = 12 bytes
    pixel_data = b''
    for i in range(total_pixels):
        # White pixel: R=1.0, G=1.0, B=1.0 as 32-bit floats
        pixel_data += struct.pack('fff', 1.0, 1.0, 1.0)
    
    # Create EXR header (simplified)
    header_data = create_exr_header(width, height)
    
    # Combine header and pixel data
    exr_data = header_data + pixel_data
    
    # Write to file
    with open(output_path, 'wb') as f:
        f.write(exr_data)
    
    print(f"Created white environment map: {output_path}")
    print(f"Dimensions: {width}x{height}")
    print(f"File size: {len(exr_data)} bytes")

def create_exr_header(width, height):
    """
    Create a minimal EXR header for a white environment map.
    This is a simplified version that should work for basic EXR files.
    """
    
    # EXR magic number
    magic = b'\x76\x2f\x31\x01'
    
    # Version and flags
    version = struct.pack('I', 2)  # Version 2
    
    # Header attributes (simplified)
    header_attrs = []
    
    # Display window
    header_attrs.append(b'displayWindow\x00' + struct.pack('iiii', 0, 0, width-1, height-1))
    
    # Data window  
    header_attrs.append(b'dataWindow\x00' + struct.pack('iiii', 0, 0, width-1, height-1))
    
    # Pixel aspect ratio
    header_attrs.append(b'pixelAspectRatio\x00' + struct.pack('f', 1.0))
    
    # Screen window center
    header_attrs.append(b'screenWindowCenter\x00' + struct.pack('ff', 0.0, 0.0))
    
    # Screen window width
    header_attrs.append(b'screenWindowWidth\x00' + struct.pack('f', 1.0))
    
    # Line order
    header_attrs.append(b'lineOrder\x00' + b'increasingY\x00')
    
    # Compression
    header_attrs.append(b'compression\x00' + b'no\x00')
    
    # Channels
    channels = b'channels\x00'
    channels += b'chlist\x00'
    channels += struct.pack('I', 3)  # 3 channels (RGB)
    
    # R channel
    channels += b'R\x00' + struct.pack('i', 1) + struct.pack('i', 0) + struct.pack('i', 0) + struct.pack('i', 0)
    
    # G channel  
    channels += b'G\x00' + struct.pack('i', 1) + struct.pack('i', 0) + struct.pack('i', 0) + struct.pack('i', 0)
    
    # B channel
    channels += b'B\x00' + struct.pack('i', 1) + struct.pack('i', 0) + struct.pack('i', 0) + struct.pack('i', 0)
    
    header_attrs.append(channels)
    
    # Combine header attributes
    header_data = b''
    for attr in header_attrs:
        header_data += attr
    
    # Null terminator
    header_data += b'\x00'
    
    # Combine magic, version, and header
    return magic + version + header_data

def create_white_env_map_tiff(width=8192, height=4096, output_path="white_env_8k.tiff"):
    """
    Create a white environment map in TIFF format as an alternative.
    This is easier to create and should work with most image processing tools.
    """
    
    # Create a simple TIFF file with white pixels
    # This is a minimal implementation
    
    # TIFF header
    tiff_header = struct.pack('<HHIIIIIIII', 
        0x4949,  # Little endian
        42,      # TIFF version
        8,       # Offset to first IFD
        1,       # Number of directory entries
        256, 4, 1, width,     # ImageWidth
        257, 4, 1, height,    # ImageLength  
        258, 3, 3, 8,         # BitsPerSample
        259, 3, 1, 1,         # Compression (none)
        262, 3, 1, 2,         # PhotometricInterpretation (RGB)
        273, 4, 1, 0,         # StripOffsets
        277, 3, 1, 3,         # SamplesPerPixel
        278, 4, 1, height,    # RowsPerStrip
        279, 4, 1, 0,         # StripByteCounts
        0                      # End of IFD
    )
    
    # Create white pixel data (RGB, 8-bit per channel)
    pixel_data = b'\xff' * (width * height * 3)
    
    # Update strip offsets and byte counts
    strip_offset = len(tiff_header) + 12  # 12 bytes for BitsPerSample values
    strip_byte_count = len(pixel_data)
    
    # Update the header with correct offsets
    tiff_data = tiff_header[:8]  # Keep magic and version
    tiff_data += struct.pack('<I', 8)  # IFD offset
    tiff_data += struct.pack('<HHIIIIIIII', 
        1,       # Number of directory entries
        256, 4, 1, width,     # ImageWidth
        257, 4, 1, height,    # ImageLength  
        258, 3, 3, 8,         # BitsPerSample
        259, 3, 1, 1,         # Compression (none)
        262, 3, 1, 2,         # PhotometricInterpretation (RGB)
        273, 4, 1, strip_offset,  # StripOffsets
        277, 3, 1, 3,         # SamplesPerPixel
        278, 4, 1, height,    # RowsPerStrip
        279, 4, 1, strip_byte_count,  # StripByteCounts
        0                      # End of IFD
    )
    tiff_data += struct.pack('<HHH', 8, 8, 8)  # BitsPerSample values
    tiff_data += pixel_data
    
    # Write to file
    with open(output_path, 'wb') as f:
        f.write(tiff_data)
    
    print(f"Created white environment map: {output_path}")
    print(f"Dimensions: {width}x{height}")
    print(f"Format: TIFF with 8-bit RGB channels")

if __name__ == "__main__":
    # Default output path
    output_path = "white_env_8k.exr"
    
    # Check if output path is provided as command line argument
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    
    # Try to create EXR first, fall back to TIFF if needed
    try:
        create_white_env_map_exr(output_path=output_path)
    except Exception as e:
        print(f"Error creating EXR file: {e}")
        print("Creating TIFF version instead...")
        tiff_path = output_path.replace('.exr', '.tiff')
        create_white_env_map_tiff(output_path=tiff_path)
