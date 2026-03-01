#!/usr/bin/env python3
"""
Video Generator 完整工作流示例

这个脚本演示了如何使用 video-generator skill 的完整流程：
1. 获取网页内容
2. 截图作为背景
3. 生成去AI味的稿件
4. TTS 生成音频和字幕
5. 合成最终视频
"""

import os
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from video_generator import VideoGenerator, humanize_text_prompt


def example_workflow():
    """完整工作流示例"""
    
    print("=" * 60)
    print("🎬 Video Generator 完整工作流示例")
    print("=" * 60)
    
    # 初始化生成器
    generator = VideoGenerator()
    
    # Step 1: 检查依赖
    print("\n📦 Step 1: 检查依赖...")
    deps = generator.check_dependencies()
    all_installed = True
    for name, installed in deps.items():
        status = "✅ 已安装" if installed else "❌ 未安装"
        print(f"   {name}: {status}")
        if not installed:
            all_installed = False
    
    if not all_installed:
        print("\n❌ 请先安装缺失的依赖")
        return
    
    # Step 2: 生成输出路径
    print("\n📁 Step 2: 准备输出目录...")
    video_path, audio_path, srt_path, bg_path = generator.generate_output_path()
    print(f"   视频将保存到: {video_path}")
    
    # Step 3: 示例内容（实际使用时从网页获取）
    print("\n📝 Step 3: 准备内容...")
    sample_content = """
    Claude 是 Anthropic 开发的 AI 助手，专注于安全和有益的人工智能。
    它可以帮助用户完成各种任务，包括写作、分析、编程等。
    Claude 的特点是能够进行自然流畅的对话，并且注重诚实和准确性。
    """
    
    # Step 4: 生成去AI味的稿件
    print("\n✍️ Step 4: 生成去AI味稿件...")
    print("   使用风格: natural (自然口语)")
    
    # 这里展示提示词模板
    prompt = humanize_text_prompt(sample_content, style="natural")
    print("\n   --- LLM 提示词 ---")
    print(prompt[:300] + "...")
    
    # 模拟 LLM 输出（实际使用时调用 LLM）
    humanized_script = """
说起来有个事儿特别有意思，最近 AI 助手越来越厉害了！

你猜怎么着，有个叫 Claude 的 AI，它是 Anthropic 公司开发的。这玩意儿可不简单，它不光能陪你聊天，还能帮你写文章、分析数据，甚至写代码！

有意思的是，这 Claude 跟别的 AI 不太一样。它特别注重安全，说话也实在，不会瞎编乱造。跟它聊天就像跟一个靠谱的朋友聊天一样，感觉挺自然的。

这事儿告诉我们，AI 技术真的在飞速发展，以后咱们的工作生活可能都会被改变。不过也别担心，AI 是来帮忙的，不是来抢饭碗的！
    """.strip()
    
    print("\n   --- 生成的稿件 ---")
    print(f"   {humanized_script[:100]}...")
    print(f"   稿件长度: {len(humanized_script)} 字")
    
    # Step 5: 创建背景
    print("\n🎨 Step 5: 创建背景...")
    bg_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 使用纯色背景作为示例
    if generator.create_solid_background(bg_path, color="#1a1a2e"):
        print(f"   ✅ 背景已创建: {bg_path}")
    else:
        print(f"   ❌ 背景创建失败")
        return
    
    # Step 6: TTS 生成音频
    print("\n🎤 Step 6: TTS 生成音频和字幕...")
    print("   使用语音: xiaoxiao (晓晓)")
    
    if generator.text_to_speech(humanized_script, audio_path, srt_path, voice="xiaoxiao"):
        print(f"   ✅ 音频已生成: {audio_path}")
        print(f"   ✅ 字幕已生成: {srt_path}")
        
        # 获取音频时长
        duration = generator.get_audio_duration(audio_path)
        print(f"   音频时长: {duration:.1f} 秒")
    else:
        print("   ❌ TTS 生成失败")
        return
    
    # Step 7: 合成视频
    print("\n🎬 Step 7: 合成最终视频...")
    
    if generator.compose_video(bg_path, audio_path, srt_path, video_path):
        print(f"   ✅ 视频已生成: {video_path}")
        
        # 获取视频大小
        video_size = video_path.stat().st_size / (1024 * 1024)
        print(f"   视频大小: {video_size:.2f} MB")
    else:
        print("   ❌ 视频合成失败")
        return
    
    # 完成
    print("\n" + "=" * 60)
    print("✅ 视频生成完成！")
    print("=" * 60)
    print(f"\n📹 输出文件:")
    print(f"   视频: {video_path}")
    print(f"   音频: {audio_path}")
    print(f"   字幕: {srt_path}")
    print(f"   背景: {bg_path}")


def test_dependencies():
    """测试依赖安装"""
    print("🔍 检查依赖安装状态...\n")
    
    generator = VideoGenerator()
    deps = generator.check_dependencies()
    
    print("依赖状态:")
    for name, installed in deps.items():
        status = "✅ 已安装" if installed else "❌ 未安装"
        print(f"  {name}: {status}")
    
    if all(deps.values()):
        print("\n✅ 所有依赖已安装，可以开始使用！")
    else:
        print("\n❌ 请安装缺失的依赖:")
        if not deps.get("ffmpeg"):
            print("  brew install ffmpeg")
        if not deps.get("edge-tts"):
            print("  uv add edge-tts")
        if not deps.get("pyyaml"):
            print("  uv add pyyaml")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Video Generator 示例")
    parser.add_argument("--test", action="store_true", help="测试依赖安装")
    parser.add_argument("--demo", action="store_true", help="运行完整示例")
    
    args = parser.parse_args()
    
    if args.test:
        test_dependencies()
    elif args.demo:
        example_workflow()
    else:
        parser.print_help()