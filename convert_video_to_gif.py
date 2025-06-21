#!/usr/bin/env python3
"""
Convert demo video to optimized GIF for GitHub display
"""

import subprocess
import sys
from pathlib import Path

def convert_to_gif():
    """Convert MP4 to optimized GIF using ffmpeg"""
    
    input_video = Path("docs/demo_video.mp4")
    output_gif = Path("docs/demo_video.gif")
    
    if not input_video.exists():
        print(f"❌ Input video not found: {input_video}")
        return False
    
    # Check if ffmpeg is available
    try:
        subprocess.run(["ffmpeg", "-version"], 
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg not found. Please install FFmpeg:")
        print("   Download from: https://ffmpeg.org/download.html")
        print("   Or use: winget install FFmpeg")
        return False
    
    print(f"🎬 Converting {input_video} to {output_gif}...")
    
    # FFmpeg command for high-quality GIF
    # - Scale to 720p for GitHub
    # - Optimize palette for better quality
    # - Reduce frame rate slightly for smaller file size
    cmd = [
        "ffmpeg", "-i", str(input_video),
        "-vf", "fps=20,scale=720:-1:flags=lanczos,palettegen=stats_mode=diff",
        "-y", "palette.png"
    ]
    
    try:
        # Generate palette
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Create GIF with palette
        cmd = [
            "ffmpeg", "-i", str(input_video), "-i", "palette.png",
            "-filter_complex", "fps=20,scale=720:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle",
            "-y", str(output_gif)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Clean up palette file
        Path("palette.png").unlink(missing_ok=True)
        
        if output_gif.exists():
            size_mb = output_gif.stat().st_size / (1024 * 1024)
            print(f"✅ GIF created successfully!")
            print(f"   📁 File: {output_gif}")
            print(f"   📊 Size: {size_mb:.1f} MB")
            
            if size_mb > 10:
                print("⚠️  Warning: GIF is quite large for GitHub.")
                print("   Consider reducing quality or duration.")
            
            return True
        else:
            print("❌ Failed to create GIF")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error: {e}")
        return False

if __name__ == "__main__":
    print("🎥 Ouroboros Ops - Video to GIF Converter")
    print("=" * 50)
    
    if convert_to_gif():
        print("\n🎉 Conversion complete!")
        print("You can now use the GIF in your README:")
        print("   ![Demo GIF](docs/demo_video.gif)")
    else:
        print("\n❌ Conversion failed. See messages above.")
