#!/usr/bin/env python3
"""
完整的视频生成工作流示例
演示如何从 URL 生成视频
"""

import asyncio
import tempfile
from pathlib import Path
from datetime import datetime

# 导入 chaobot 工具
from chaobot.agent.tools.web import WebFetchTool
from chaobot.agent.tools.file import FileWriteTool
from chaobot.config import Config

# 导入视频生成器
from video_generator import VideoGenerator


async def generate_video_from_url(
    url: str,
    style: str = "normal",
    voice: str = "xiaoxiao",
    background: str = None
):
    """
    从 URL 生成视频的完整流程
    
    Args:
        url: 网页 URL
        style: 风格 (normal/news/tutorial/humorous)
        voice: 语音
        background: 背景图片/视频路径
    
    Returns:
        生成的视频路径
    """
    print(f"🎬 开始生成视频: {url}")
    
    # 1. 初始化工具
    config = Config.load()
    web_fetch = WebFetchTool(config)
    video_gen = VideoGenerator()
    
    # 2. 检查依赖
    deps = video_gen.check_dependencies()
    if not all(deps.values()):
        missing = [k for k, v in deps.items() if not v]
        raise RuntimeError(f"缺少依赖: {missing}")
    
    print("✅ 依赖检查通过")
    
    # 3. 抓取网页内容
    print("📥 抓取网页内容...")
    result = await web_fetch.execute(url=url)
    if not result.success:
        raise RuntimeError(f"抓取失败: {result.output}")
    
    content = result.output
    print(f"✅ 获取内容 ({len(content)} 字符)")
    
    # 4. 生成稿件 (这里需要 LLM，暂时用简化版本)
    print("✍️ 生成稿件...")
    script = generate_script(content, style)
    print(f"✅ 稿件生成完成 ({len(script)} 字)")
    
    # 5. 生成 TTS 和字幕
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        audio_path = tmpdir / "audio.mp3"
        subtitle_path = tmpdir / "subtitle.vtt"
        
        print("🔊 生成语音...")
        await video_gen.generate_tts_with_subtitles(
            script, audio_path, subtitle_path, voice=voice
        )
        print("✅ 语音生成完成")
        
        # 6. 准备背景
        if background:
            bg_path = Path(background)
        else:
            bg_path = video_gen.get_random_background()
            if not bg_path:
                # 创建默认背景
                bg_path = tmpdir / "bg.png"
                import subprocess
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", 
                    "-i", "color=c=black:s=1920x1080:d=1",
                    str(bg_path)
                ], check=True, capture_output=True)
                print("ℹ️ 使用默认黑色背景")
        
        # 7. 合成视频
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        output_video = video_gen.output_dir / f"{timestamp}.mp4"
        
        print("🎥 合成视频...")
        video_gen.create_video_with_image(
            bg_path, audio_path, output_video, subtitle_path
        )
        
        print(f"✅ 视频生成完成: {output_video}")
        return output_video


def generate_script(content: str, style: str = "normal") -> str:
    """
    根据内容和风格生成视频稿件
    
    注意：这个函数应该由 LLM 来完成
    这里只是一个简化的示例
    
    Args:
        content: 原始内容
        style: 风格
    
    Returns:
        生成的稿件
    """
    # 这里应该调用 LLM API 来生成稿件
    # 简化版本：直接截取前 500 字
    
    # 移除多余的空白
    content = ' '.join(content.split())
    
    # 根据风格调整
    if style == "news":
        prefix = "各位观众大家好，今天我们来看一条重要新闻。"
        suffix = "以上就是今天的新闻内容，感谢收看。"
    elif style == "tutorial":
        prefix = "大家好，今天我们来学习一个新的知识点。"
        suffix = "希望这个教程对你有帮助，我们下期再见！"
    elif style == "humorous":
        prefix = "嘿，大家好！今天有个有趣的事情要分享。"
        suffix = "哈哈，是不是很有趣？别忘了点赞关注哦！"
    else:
        prefix = "大家好，欢迎观看本期视频。"
        suffix = "感谢观看，我们下期再见！"
    
    # 截取内容（保持句子完整）
    max_length = 400
    if len(content) > max_length:
        # 在句号、问号、感叹号处截断
        for i in range(max_length, 0, -1):
            if content[i] in '。！？.!?'：
                content = content[:i+1]
                break
        else:
            content = content[:max_length] + "..."
    
    return f"{prefix}\n\n{content}\n\n{suffix}"


async def main():
    """示例：从 URL 生成视频"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python example_workflow.py <URL>")
        print("示例: python example_workflow.py https://example.com/article")
        sys.exit(1)
    
    url = sys.argv[1]
    
    try:
        video_path = await generate_video_from_url(
            url=url,
            style="normal",
            voice="xiaoxiao"
        )
        print(f"\n🎉 成功！视频已保存到: {video_path}")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())