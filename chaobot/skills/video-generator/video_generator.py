#!/usr/bin/env python3
"""
Video Generator - 从网页生成视频
支持配置文件、多种风格、自定义背景
"""

import os
import re
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import yaml


class VideoGenerator:
    """视频生成器主类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化生成器，加载配置"""
        self.workspace = Path.home() / ".chaobot" / "workspace"
        self.output_dir = self.workspace / "videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 语音映射
        self.voices = {
            "xiaoxiao": "zh-CN-XiaoxiaoNeural",
            "xiaoyi": "zh-CN-XiaoyiNeural",
            "yunxi": "zh-CN-YunxiNeural",
            "yunyang": "zh-CN-YunyangNeural",
            "yunjian": "zh-CN-YunjianNeural",
        }
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件"""
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        else:
            config_path = Path(config_path)
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            "voice": {"default": "xiaoxiao"},
            "writing_styles": {"default": "natural"},
            "video": {
                "resolution": "1920x1080",
                "subtitle": {
                    "font": "PingFang SC",
                    "font_size": 24,
                    "color": "white",
                    "outline": 2
                }
            },
            "content": {
                "min_length": 200,
                "max_length": 800,
                "ideal_length": 400
            }
        }
    
    def generate_output_path(self, prefix: str = "") -> tuple:
        """生成输出文件路径"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        index = 1
        while True:
            filename = f"{date_str}_{index:03d}"
            if prefix:
                filename = f"{prefix}_{filename}"
            video_path = self.output_dir / f"{filename}.mp4"
            if not video_path.exists():
                break
            index += 1
        
        return (
            video_path,
            self.output_dir / f"{filename}.mp3",
            self.output_dir / f"{filename}.srt",
            self.output_dir / "backgrounds" / f"{filename}.png"
        )
    
    def text_to_speech(
        self, 
        text: str, 
        output_audio: Path,
        output_srt: Path,
        voice: str = "xiaoxiao"
    ) -> bool:
        """使用 edge-tts 生成语音和字幕"""
        voice_id = self.voices.get(voice, self.voices["xiaoxiao"])
        
        # 先生成 VTT 字幕
        vtt_path = output_srt.with_suffix('.vtt')
        
        cmd = [
            "edge-tts",
            "--text", text,
            "--voice", voice_id,
            "--write-media", str(output_audio),
            "--write-subtitles", str(vtt_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            
            # 转换 VTT 为 SRT
            self._vtt_to_srt(vtt_path, output_srt)
            
            # 删除 VTT 文件
            vtt_path.unlink(missing_ok=True)
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"TTS 生成失败: {e}")
            return False
    
    def _vtt_to_srt(self, vtt_path: Path, srt_path: Path):
        """转换 VTT 字幕为 SRT 格式"""
        with open(vtt_path, 'r', encoding='utf-8') as f:
            vtt_content = f.read()
        
        # 移除 VTT 头部
        lines = vtt_content.strip().split('\n')
        srt_lines = []
        index = 1
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            # 查找时间轴
            if '-->' in line:
                # 转换时间格式 (00:00:00.000 -> 00:00:00,000)
                time_line = line.replace('.', ',')
                srt_lines.append(str(index))
                srt_lines.append(time_line)
                index += 1
                i += 1
                # 获取字幕文本
                while i < len(lines) and lines[i].strip():
                    srt_lines.append(lines[i].strip())
                    i += 1
                srt_lines.append('')
            i += 1
        
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(srt_lines))
    
    def create_solid_background(self, output_path: Path, color: str = "#1a1a2e"):
        """创建纯色背景"""
        resolution = self.config.get("video", {}).get("resolution", "1920x1080")
        width, height = resolution.split('x')
        
        cmd = [
            "ffmpeg", "-f", "lavfi",
            "-i", f"color=c={color}:s={width}x{height}:d=1",
            "-frames:v", "1",
            "-y", str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def compose_video(
        self,
        background: Path,
        audio: Path,
        subtitle: Path,
        output: Path
    ) -> bool:
        """合成最终视频"""
        subtitle_config = self.config.get("video", {}).get("subtitle", {})
        font = subtitle_config.get("font", "PingFang SC")
        font_size = subtitle_config.get("font_size", 24)
        
        # 构建字幕滤镜
        subtitle_filter = (
            f"subtitles={subtitle.absolute()}:"
            f"force_style='FontName={font},FontSize={font_size},"
            f"PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2,MarginV=50'"
        )
        
        # 第一步：合成视频（无字幕）
        temp_video = output.with_suffix('.temp.mp4')
        cmd1 = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(background),
            "-i", str(audio),
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(temp_video)
        ]
        
        try:
            subprocess.run(cmd1, check=True, capture_output=True)
            
            # 第二步：添加字幕
            cmd2 = [
                "ffmpeg", "-y",
                "-i", str(temp_video),
                "-vf", subtitle_filter,
                "-c:a", "copy",
                str(output)
            ]
            
            subprocess.run(cmd2, check=True, capture_output=True)
            
            # 删除临时文件
            temp_video.unlink(missing_ok=True)
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"视频合成失败: {e}")
            return False
    
    def get_audio_duration(self, audio_path: Path) -> float:
        """获取音频时长"""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            str(audio_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            data = json.loads(result.stdout)
            return float(data["format"]["duration"])
        except Exception:
            return 0.0
    
    def check_dependencies(self) -> Dict[str, bool]:
        """检查依赖是否安装"""
        dependencies = {}
        
        # 检查 ffmpeg
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True)
            dependencies["ffmpeg"] = True
        except FileNotFoundError:
            dependencies["ffmpeg"] = False
        
        # 检查 edge-tts
        try:
            subprocess.run(["edge-tts", "--version"], capture_output=True)
            dependencies["edge-tts"] = True
        except FileNotFoundError:
            dependencies["edge-tts"] = False
        
        # 检查 Python 包
        try:
            import yaml
            dependencies["pyyaml"] = True
        except ImportError:
            dependencies["pyyaml"] = False
        
        return dependencies


def humanize_text_prompt(content: str, style: str = "natural") -> str:
    """生成去 AI 味的写作提示词"""
    
    style_prompts = {
        "natural": """
你是一位视频内容创作者，擅长用自然、口语化的方式讲述内容。

请将以下内容改写成适合视频解说的稿件：

要求：
1. 像和朋友聊天一样，轻松自然
2. 避免使用"首先、其次、最后、综上所述"等 AI 味词汇
3. 用故事化的方式串联内容
4. 保持 200-400 字的精炼长度
5. 开头要吸引人，结尾要有互动感
6. 直接输出稿件内容，不要加任何解释

避免的词汇：
- 首先、其次、再次、最后
- 综上所述、总而言之
- 值得注意的是、不可否认
- 显而易见、毋庸置疑
- 此外、另外、不仅如此

推荐的表达：
- "说起来有个事儿..."
- "你猜怎么着..."
- "有意思的是..."
- "这事儿告诉我们..."

内容：
{content}
""",
        "storytelling": """
你是一位擅长讲故事的视频创作者。

请将以下内容改写成引人入胜的故事风格稿件：

要求：
1. 用故事化的方式呈现
2. 制造悬念和转折
3. 200-400 字
4. 直接输出稿件

内容：
{content}
""",
        "news": """
你是一位新闻主播。

请将以下内容改写成新闻播报风格的稿件：

要求：
1. 简洁、专业
2. 突出重点信息
3. 200-400 字
4. 直接输出稿件

内容：
{content}
""",
        "humorous": """
你是一位幽默风趣的视频博主。

请将以下内容改写成轻松搞笑的风格：

要求：
1. 加入幽默元素
2. 用轻松的口吻
3. 200-400 字
4. 直接输出稿件

内容：
{content}
""",
        "professional": """
你是一位专业领域的视频创作者。

请将以下内容改写成专业解读风格：

要求：
1. 深度分析
2. 专业视角
3. 200-400 字
4. 直接输出稿件

内容：
{content}
"""
    }
    
    template = style_prompts.get(style, style_prompts["natural"])
    return template.format(content=content)


if __name__ == "__main__":
    # 测试依赖
    generator = VideoGenerator()
    deps = generator.check_dependencies()
    
    print("依赖检查:")
    for name, installed in deps.items():
        status = "✅ 已安装" if installed else "❌ 未安装"
        print(f"  {name}: {status}")
    
    if not all(deps.values()):
        print("\n请安装缺失的依赖:")
        if not deps.get("ffmpeg"):
            print("  brew install ffmpeg")
        if not deps.get("edge-tts"):
            print("  pip install edge-tts")
        if not deps.get("pyyaml"):
            print("  pip install pyyaml")
    else:
        print("\n✅ 所有依赖已安装，可以开始使用！")