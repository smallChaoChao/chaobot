#!/usr/bin/env python3
"""
Video Generator - Generate video from script with TTS and subtitles.

Usage:
    python generate_video.py --script "你的脚本内容" --output-dir /path/to/output
    python generate_video.py --script-file script.txt --output-dir /path/to/output
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: Path | None = None) -> tuple[bool, str]:
    """Run a shell command and return success status and output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Error: {e.stderr}"


def generate_audio_and_subtitles(
    script: str,
    output_dir: Path,
    voice: str = "zh-CN-XiaoxiaoNeural",
    rate: str = "+10%"
) -> tuple[bool, str]:
    """Generate audio and subtitles using edge-tts."""
    print("🎵 Generating audio and subtitles...")

    audio_path = output_dir / "audio.mp3"
    vtt_path = output_dir / "subtitles.vtt"
    srt_path = output_dir / "subtitles.srt"

    # Clean script (remove newlines for TTS)
    clean_script = script.replace('\n', ' ').strip()

    # Generate audio and VTT subtitles
    cmd = [
        "edge-tts",
        "--voice", voice,
        "--text", clean_script,
        "--write-media", str(audio_path),
        "--write-subtitles", str(vtt_path),
        "--rate", rate
    ]

    success, output = run_command(cmd)
    if not success:
        return False, f"Failed to generate audio: {output}"

    # Convert VTT to SRT
    if vtt_path.exists():
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(vtt_path),
            str(srt_path)
        ]
        success, output = run_command(cmd)
        if not success:
            return False, f"Failed to convert subtitles: {output}"

        # Remove VTT file
        vtt_path.unlink()

    print(f"  ✓ Audio: {audio_path}")
    print(f"  ✓ Subtitles: {srt_path}")
    return True, ""


def create_black_background(output_dir: Path, resolution: str = "1920x1080") -> tuple[bool, str]:
    """Create a black background image."""
    print("🎨 Creating black background...")

    bg_path = output_dir / "background.png"

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", f"color=c=black:s={resolution}:d=1",
        "-frames:v", "1",
        str(bg_path)
    ]

    success, output = run_command(cmd)
    if not success:
        return False, f"Failed to create background: {output}"

    print(f"  ✓ Background: {bg_path}")
    return True, ""


def compose_video(output_dir: Path) -> tuple[bool, str]:
    """Compose final video with audio and subtitles."""
    print("🎬 Composing final video...")

    bg_path = output_dir / "background.png"
    audio_path = output_dir / "audio.mp3"
    srt_path = output_dir / "subtitles.srt"
    temp_video = output_dir / "temp_video.mp4"
    final_video = output_dir / "final_video.mp4"

    # Step 1: Combine background and audio
    cmd = [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-i", str(bg_path),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(temp_video)
    ]

    success, output = run_command(cmd)
    if not success:
        return False, f"Failed to combine video and audio: {output}"

    # Step 2: Add subtitles
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(temp_video),
        "-vf",
        "subtitles=" + str(srt_path) + ":force_style='FontName=PingFang SC,FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2,MarginV=50'",
        "-c:a", "copy",
        str(final_video)
    ]

    success, output = run_command(cmd)
    if not success:
        return False, f"Failed to add subtitles: {output}"

    # Clean up temp file
    temp_video.unlink(missing_ok=True)

    print(f"  ✓ Final video: {final_video}")
    return True, ""


def main():
    parser = argparse.ArgumentParser(description="Generate video from script")
    parser.add_argument("--script", type=str, help="Video script content")
    parser.add_argument("--script-file", type=str, help="Path to script file")
    parser.add_argument("--output-dir", type=str, required=True, help="Output directory")
    parser.add_argument("--voice", type=str, default="zh-CN-XiaoxiaoNeural",
                        help="TTS voice (default: zh-CN-XiaoxiaoNeural)")
    parser.add_argument("--rate", type=str, default="+10%",
                        help="Speech rate (default: +10%)")

    args = parser.parse_args()

    # Get script content
    if args.script:
        script = args.script
    elif args.script_file:
        script = Path(args.script_file).read_text(encoding="utf-8")
    else:
        print("Error: Either --script or --script-file must be provided")
        sys.exit(1)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📁 Output directory: {output_dir}")
    print(f"📝 Script length: {len(script)} characters")

    # Step 1: Generate audio and subtitles
    success, error = generate_audio_and_subtitles(
        script,
        output_dir,
        voice=args.voice,
        rate=args.rate
    )
    if not success:
        print(f"❌ {error}")
        sys.exit(1)

    # Step 2: Create black background
    success, error = create_black_background(output_dir)
    if not success:
        print(f"❌ {error}")
        sys.exit(1)

    # Step 3: Compose final video
    success, error = compose_video(output_dir)
    if not success:
        print(f"❌ {error}")
        sys.exit(1)

    print("\n✅ Video generation complete!")
    print(f"   Output: {output_dir / 'final_video.mp4'}")


if __name__ == "__main__":
    main()
