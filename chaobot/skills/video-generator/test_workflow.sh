#!/bin/bash
# Video Generator 测试脚本

set -e

echo "=========================================="
echo "🎬 Video Generator 测试"
echo "=========================================="

# 设置工作目录
WORKSPACE="$HOME/.chaobot/workspace/videos"
mkdir -p "$WORKSPACE/backgrounds"

# 测试文件
DATE=$(date +%Y-%m-%d)
OUTPUT="$WORKSPACE/${DATE}_test"
AUDIO="$OUTPUT.mp3"
SRT="$OUTPUT.srt"
VTT="$OUTPUT.vtt"
BG="$WORKSPACE/backgrounds/${DATE}_test.png"
VIDEO="$OUTPUT.mp4"

echo ""
echo "📁 输出目录: $WORKSPACE"
echo "📄 输出文件: $OUTPUT"

# Step 1: 测试 edge-tts
echo ""
echo "🎤 Step 1: 测试 edge-tts..."
TEST_TEXT="说起来有个事儿特别有意思，最近 AI 助手越来越厉害了！你猜怎么着，有个叫 Claude 的 AI，它是 Anthropic 公司开发的。这玩意儿可不简单，它不光能陪你聊天，还能帮你写文章、分析数据，甚至写代码！"

uv run edge-tts --text "$TEST_TEXT" \
    --voice zh-CN-XiaoxiaoNeural \
    --write-media "$AUDIO" \
    --write-subtitles "$VTT"

if [ -f "$AUDIO" ]; then
    echo "   ✅ 音频生成成功: $AUDIO"
    echo "   文件大小: $(ls -lh "$AUDIO" | awk '{print $5}')"
else
    echo "   ❌ 音频生成失败"
    exit 1
fi

# Step 2: 转换字幕格式
echo ""
echo "📝 Step 2: 转换字幕格式..."
if [ -f "$VTT" ]; then
    # 简单转换 VTT 到 SRT
    uv run python -c "
import sys
vtt_file = '$VTT'
srt_file = '$SRT'

with open(vtt_file, 'r') as f:
    lines = f.readlines()

srt_lines = []
index = 1
i = 0
while i < len(lines):
    line = lines[i].strip()
    if '-->' in line:
        time_line = line.replace('.', ',')
        srt_lines.append(str(index))
        srt_lines.append(time_line)
        index += 1
        i += 1
        while i < len(lines) and lines[i].strip():
            srt_lines.append(lines[i].strip())
            i += 1
        srt_lines.append('')
    i += 1

with open(srt_file, 'w') as f:
    f.write('\n'.join(srt_lines))

print(f'   ✅ 字幕转换成功: {srt_file}')
"
    rm -f "$VTT"
else
    echo "   ⚠️ 没有生成字幕文件"
fi

# Step 3: 创建背景图片
echo ""
echo "🎨 Step 3: 创建背景图片..."
ffmpeg -f lavfi -i color=c=#1a1a2e:s=1920x1080:d=1 \
    -frames:v 1 -y "$BG" 2>/dev/null

if [ -f "$BG" ]; then
    echo "   ✅ 背景创建成功: $BG"
else
    echo "   ❌ 背景创建失败"
    exit 1
fi

# Step 4: 获取音频时长
echo ""
echo "⏱️ Step 4: 获取音频时长..."
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO")
echo "   音频时长: ${DURATION}s"

# Step 5: 合成视频
echo ""
echo "🎬 Step 5: 合成视频..."

# 先合成无字幕视频
TEMP_VIDEO="${OUTPUT}_temp.mp4"
ffmpeg -y -loop 1 -i "$BG" -i "$AUDIO" \
    -c:v libx264 -tune stillimage -c:a aac -b:a 192k \
    -pix_fmt yuv420p -shortest "$TEMP_VIDEO" 2>/dev/null

if [ ! -f "$TEMP_VIDEO" ]; then
    echo "   ❌ 视频合成失败"
    exit 1
fi

# 添加字幕
if [ -f "$SRT" ]; then
    # 需要转义 SRT 路径中的特殊字符
    SRT_ESCAPED=$(echo "$SRT" | sed 's/:/\\:/g')
    ffmpeg -y -i "$TEMP_VIDEO" \
        -vf "subtitles='${SRT_ESCAPED}':force_style='FontName=PingFang SC,FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2,MarginV=50'" \
        -c:a copy "$VIDEO" 2>/dev/null
else
    mv "$TEMP_VIDEO" "$VIDEO"
fi

rm -f "$TEMP_VIDEO"

if [ -f "$VIDEO" ]; then
    echo "   ✅ 视频生成成功: $VIDEO"
    echo "   文件大小: $(ls -lh "$VIDEO" | awk '{print $5}')"
else
    echo "   ❌ 视频生成失败"
    exit 1
fi

# 完成
echo ""
echo "=========================================="
echo "✅ 测试完成！"
echo "=========================================="
echo ""
echo "📹 生成的文件:"
echo "   视频: $VIDEO"
echo "   音频: $AUDIO"
echo "   字幕: $SRT"
echo "   背景: $BG"
echo ""
echo "💡 可以用以下命令播放视频:"
echo "   open '$VIDEO'"