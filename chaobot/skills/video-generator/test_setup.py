#!/usr/bin/env python3
"""
测试视频生成环境是否正确配置
"""

import subprocess
import sys


def check_command(cmd: str) -> tuple[bool, str]:
    """检查命令是否可用"""
    try:
        result = subprocess.run(
            [cmd, "-version"] if cmd != "edge-tts" else ["edge-tts", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return True, result.stdout.split('\n')[0] if result.stdout else "OK"
    except FileNotFoundError:
        return False, "未安装"
    except subprocess.TimeoutExpired:
        return False, "超时"
    except Exception as e:
        return False, str(e)


def check_python_package(package: str) -> tuple[bool, str]:
    """检查 Python 包是否安装"""
    try:
        module = package.replace("-", "_")
        mod = __import__(module)
        version = getattr(mod, "__version__", "unknown")
        return True, version
    except ImportError:
        return False, "未安装"


def main():
    """检查所有依赖"""
    print("🔍 检查视频生成环境...\n")
    
    all_ok = True
    
    # 检查 FFmpeg
    print("1️⃣  FFmpeg")
    ok, info = check_command("ffmpeg")
    status = "✅" if ok else "❌"
    print(f"   {status} {info}")
    if not ok:
        print("   安装: brew install ffmpeg (macOS)")
        print("         sudo apt install ffmpeg (Ubuntu)")
        all_ok = False
    
    print()
    
    # 检查 edge-tts
    print("2️⃣  Edge-TTS")
    ok, info = check_python_package("edge-tts")
    status = "✅" if ok else "❌"
    print(f"   {status} {info}")
    if not ok:
        print("   安装: pip install edge-tts")
        all_ok = False
    
    print()
    
    # 检查可选依赖
    print("3️⃣  可选依赖")
    
    # Pillow
    ok, info = check_python_package("Pillow")
    status = "✅" if ok else "⚠️ "
    print(f"   {status} Pillow: {info} (用于生成背景图片)")
    
    print()
    
    # 检查目录
    print("4️⃣  工作目录")
    from pathlib import Path
    
    videos_dir = Path.home() / ".chaobot" / "workspace" / "videos"
    bg_dir = Path.home() / ".chaobot" / "workspace" / "backgrounds"
    
    videos_dir.mkdir(parents=True, exist_ok=True)
    bg_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"   ✅ 视频输出目录: {videos_dir}")
    print(f"   ✅ 背景资源目录: {bg_dir}")
    
    # 检查背景文件
    backgrounds = list(bg_dir.glob("*"))
    if backgrounds:
        print(f"   ℹ️  已有 {len(backgrounds)} 个背景文件")
    else:
        print("   ⚠️  没有背景文件，将使用默认黑色背景")
        print("   提示: 添加背景图片/视频到背景目录")
    
    print()
    
    # 总结
    if all_ok:
        print("🎉 环境检查通过！可以开始生成视频了！")
        print("\n快速测试:")
        print('  edge-tts --text "你好，这是一个测试" --write-media test.mp3')
    else:
        print("⚠️  部分依赖缺失，请先安装")
        print("\n安装命令:")
        print("  pip install edge-tts")
        print("  brew install ffmpeg  # macOS")
        print("  sudo apt install ffmpeg  # Ubuntu")
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())