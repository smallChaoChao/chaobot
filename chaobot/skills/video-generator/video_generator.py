#!/usr/bin/env python3
"""
Video Generator Helper Script
帮助生成视频的辅助脚本
"""

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Optional
import tempfile
import json


class VideoGenerator:
    """视频生成器类"""
    
    # 可用的中文语音
    CHINESE_VOICES = {
        "xiaoxiao": "zh-CN-XiaoxiaoNeural",  # 晓晓 - 女声，温柔
        "xiaoyi": "zh-CN-XiaoyiNeural",      # 晓伊 - 女声，活泼
        "yunxi": "zh-CN-YunxiNeural",        # 云希 - 男声，年轻
        "yunyang": "zh-CN-YunyangNeural",    # 云扬 - 男声，新闻播报
        "yunjian": "zh-CN-YunjianNeural",    # 云健 - 男声，沉稳
    }
    
    # 可用的英文语音
    ENGLISH_VOICES = {
        "jenny": "en-US-JennyNeural",        # Jenny - 女声，自然
        "guy": "en-US-GuyNeural",            # Guy - 男声，专业
        "sonia": "en-GB-SoniaNeural",        # Sonia - 女声，英式
    }
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        初始化视频生成器
        
        Args:
            output_dir: 输出目录，默认为 ~/.chaobot/workspace/videos/
        """
        if output_dir is None:
            output_dir = Path.home() / ".chaobot" / "workspace" / "videos"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 背景目录
        self.bg_dir = Path.home() / ".chaobot" / "workspace" / "backgrounds"
        self.bg_dir.mkdir(parents=True, exist_ok=True)
    
    def check_dependencies(self) -> dict:
        """检查依赖是否安装"""
        deps = {
            "ffmpeg": self._check_command("ffmpeg"),
            "edge-tts": self._check_command("edge-tts") or self._check_python_package("edge-tts"),
        }
        return deps
    
    def _check_command(self, cmd: str) -> bool:
        """检查命令是否可用"""
        try:
            subprocess.run([cmd, "-version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_python_package(self, package: str) -> bool:
        """检查 Python 包是否安装"""
        try:
            __import__(package.replace("-", "_"))
            return True
        except ImportError:
            return False
    
    async def generate_tts(
        self,
        text: str,
        output_audio: Path,
        voice: str = "xiaoxiao",
        language: str = "zh"
    ) -> Path:
        """
        生成 TTS 音频
        
        Args:
            text: 要转换的文本
            output_audio: 输出音频文件路径
            voice: 语音名称
            language: 语言 (zh/en)
        
        Returns:
            生成的音频文件路径
        """
        # 获取语音 ID
        if language == "zh":
            voice_id = self.CHINESE_VOICES.get(voice, self.CHINESE_VOICES["xiaoxiao"])
        else:
            voice_id = self.ENGLISH_VOICES.get(voice, self.ENGLISH_VOICES["jenny"])
        
        # 使用 edge-tts 生成音频
        import edge_tts
        
        communicate = edge_tts.Communicate(text, voice_id)
        await communicate.save(str(output_audio))
        
        return output_audio
    
    async def generate_tts_with_subtitles(
        self,
        text: str,
        output_audio: Path,
        output_subtitle: Path,
        voice: str = "xiaoxiao",
        language: str = "zh"
    ) -> tuple[Path, Path]:
        """
        生成 TTS 音频和字幕
        
        Args:
            text: 要转换的文本
            output_audio: 输出音频文件路径
            output_subtitle: 输出字幕文件路径
            voice: 语音名称
            language: 语言
        
        Returns:
            (音频路径, 字幕路径)
        """
        voice_id = self.CHINESE_VOICES.get(voice, self.CHINESE_VOICES["xiaoxiao"])
        
        import edge_tts
        
        communicate = edge_tts.Communicate(text, voice_id)
        
        # 生成音频和字幕
        submaker = edge_tts.SubMaker()
        
        with open(output_audio, "wb") as audio_file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    submaker.feed(chunk)
        
        # 保存字幕
        with open(output_subtitle, "w", encoding="utf-8") as sub_file:
            sub_file.write(submaker.generate_subs())
        
        return output_audio, output_subtitle
    
    def create_video_with_image(
        self,
        image_path: Path,
        audio_path: Path,
        output_video: Path,
        subtitle_path: Optional[Path] = None,
        quality: str = "medium"
    ) -> Path:
        """
        使用图片和音频创建视频
        
        Args:
            image_path: 背景图片路径
            audio_path: 音频文件路径
            output_video: 输出视频路径
            subtitle_path: 字幕文件路径
            quality: 质量 (low/medium/high)
        
        Returns:
            生成的视频路径
        """
        # 质量设置
        crf_map = {"low": 28, "medium": 23, "high": 18}
        crf = crf_map.get(quality, 23)
        
        # 构建命令
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-crf", str(crf),
            "-shortest",
        ]
        
        # 添加字幕
        if subtitle_path and subtitle_path.exists():
            # 创建临时视频，然后添加字幕
            temp_video = output_video.with_suffix(".temp.mp4")
            cmd.extend(["-movflags", "+faststart", str(temp_video)])
            
            subprocess.run(cmd, check=True)
            
            # 添加字幕
            subtitle_cmd = [
                "ffmpeg", "-y",
                "-i", str(temp_video),
                "-vf", f"subtitles={str(subtitle_path)}",
                "-c:a", "copy",
                str(output_video)
            ]
            subprocess.run(subtitle_cmd, check=True)
            
            # 删除临时文件
            temp_video.unlink()
        else:
            cmd.extend(["-movflags", "+faststart", str(output_video)])
            subprocess.run(cmd, check=True)
        
        return output_video
    
    def create_video_with_background(
        self,
        background_video: Path,
        audio_path: Path,
        output_video: Path,
        subtitle_path: Optional[Path] = None
    ) -> Path:
        """
        使用背景视频和音频创建视频
        
        Args:
            background_video: 背景视频路径
            audio_path: 音频文件路径
            output_video: 输出视频路径
            subtitle_path: 字幕文件路径
        
        Returns:
            生成的视频路径
        """
        cmd = [
            "ffmpeg", "-y",
            "-i", str(background_video),
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_video)
        ]
        
        subprocess.run(cmd, check=True)
        
        # 添加字幕
        if subtitle_path and subtitle_path.exists():
            temp_video = output_video.with_suffix(".temp.mp4")
            output_video.rename(temp_video)
            
            subtitle_cmd = [
                "ffmpeg", "-y",
                "-i", str(temp_video),
                "-vf", f"subtitles={str(subtitle_path)}",
                "-c:a", "copy",
                str(output_video)
            ]
            subprocess.run(subtitle_cmd, check=True)
            temp_video.unlink()
        
        return output_video
    
    def list_backgrounds(self) -> list[Path]:
        """列出可用的背景"""
        backgrounds = []
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.mp4", "*.mov"]:
            backgrounds.extend(self.bg_dir.glob(ext))
        return backgrounds
    
    def get_random_background(self) -> Optional[Path]:
        """获取随机背景"""
        import random
        backgrounds = self.list_backgrounds()
        if backgrounds:
            return random.choice(backgrounds)
        return None


async def main():
    """示例用法"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python video_generator.py <text>")
        print("Example: python video_generator.py '大家好，欢迎观看本期视频'")
        sys.exit(1)
    
    text = sys.argv[1]
    
    generator = VideoGenerator()
    
    # 检查依赖
    deps = generator.check_dependencies()
    print(f"Dependencies: {deps}")
    
    if not deps["edge-tts"]:
        print("Error: edge-tts not installed. Run: pip install edge-tts")
        sys.exit(1)
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        audio_path = tmpdir / "audio.mp3"
        subtitle_path = tmpdir / "subtitle.vtt"
        output_video = generator.output_dir / "output.mp4"
        
        print("Generating TTS...")
        await generator.generate_tts_with_subtitles(
            text, audio_path, subtitle_path, voice="xiaoxiao"
        )
        
        # 获取背景
        background = generator.get_random_background()
        if not background:
            # 创建一个简单的背景图片
            print("No background found, creating default...")
            background = tmpdir / "bg.png"
            # 这里可以用 PIL 创建一个简单的背景
            # 现在先用纯色背景
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1920x1080:d=1",
                str(background)
            ], check=True)
        
        print("Creating video...")
        generator.create_video_with_image(
            background, audio_path, output_video, subtitle_path
        )
        
        print(f"Video created: {output_video}")


if __name__ == "__main__":
    asyncio.run(main())