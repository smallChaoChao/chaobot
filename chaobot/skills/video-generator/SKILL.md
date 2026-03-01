---
name: video-generator
description: "Generate videos from web content. Fetch content from URLs, convert to script, generate TTS audio, and create video with subtitles."
homepage: https://github.com/smallChaoChao/chaobot
metadata: {"chaobot":{"emoji":"🎬","requires":{"bins":["ffmpeg","edge-tts"]}}}
---

# Video Generator Skill

Generate professional videos from web content automatically. This skill can:
1. Fetch content from specified URLs
2. Convert content to video script using LLM
3. Generate TTS audio (Text-to-Speech)
4. Create video with subtitles and background

## ⚠️ Prerequisites

Before using this skill, ensure the following tools are installed:

### 1. FFmpeg
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows (using winget)
winget install ffmpeg
```

### 2. Edge-TTS (Microsoft Edge TTS)
```bash
pip install edge-tts
```

### 3. Optional: Background Videos/Images
Prepare some background videos or images in `~/.chaobot/workspace/backgrounds/`

## Usage

### Basic Video Generation

```bash
# Generate video from URL
chaobot run -m "生成视频：https://example.com/article"

# Generate video with custom style
chaobot run -m "用解说风格生成视频：https://news.site.com/story"
```

### Workflow

When user requests video generation, follow these steps:

#### Step 1: Fetch Web Content
```
Use web_fetch tool to get the content from the URL
Extract main text content
```

#### Step 2: Generate Script
```
Use LLM to convert content into video script:
- Keep it concise (300-500 words for 1-2 minute video)
- Use conversational tone
- Add natural pauses
- Structure into clear sections
```

#### Step 3: Generate TTS Audio
```bash
# Use edge-tts to generate audio
edge-tts --text "你的文稿内容" --write-media output.mp3

# With specific voice
edge-tts --text "你的文稿内容" --voice zh-CN-XiaoxiaoNeural --write-media output.mp3

# Available Chinese voices:
# zh-CN-XiaoxiaoNeural - 晓晓 (女声，温柔)
# zh-CN-YunxiNeural - 云希 (男声，年轻)
# zh-CN-YunyangNeural - 云扬 (男声，新闻播报)
# zh-CN-XiaoyiNeural - 晓伊 (女声，活泼)
```

#### Step 4: Create Subtitles
```bash
# Generate SRT subtitles (use whisper or manual timing)
# Or use edge-tts to get word boundaries
edge-tts --text "你的文稿内容" --write-media output.mp3 --write-subtitles output.vtt
```

#### Step 5: Compose Video
```bash
# Create video with background image and audio
ffmpeg -loop 1 -i background.jpg -i audio.mp3 -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest output.mp4

# Add subtitles
ffmpeg -i output.mp4 -vf "subtitles=subtitle.srt" final.mp4

# With background video
ffmpeg -i background.mp4 -i audio.mp3 -c:v libx264 -c:a aac -shortest output.mp4
```

## Script Template

Use this template for generating video scripts:

```markdown
## 视频标题

[开场白 - 吸引注意力]
大家好，今天我们来聊聊...

[核心内容 - 分3-5个要点]
首先，...
其次，...
最后，...

[总结与结尾]
总结一下，...
感谢观看，我们下期再见！
```

## Available Voices

### Chinese (Mandarin)
| Voice ID | Name | Gender | Style |
|----------|------|--------|-------|
| zh-CN-XiaoxiaoNeural | 晓晓 | Female | 温柔、自然 |
| zh-CN-XiaoyiNeural | 晓伊 | Female | 活泼、可爱 |
| zh-CN-YunxiNeural | 云希 | Male | 年轻、阳光 |
| zh-CN-YunyangNeural | 云扬 | Male | 新闻播报 |
| zh-CN-YunjianNeural | 云健 | Male | 沉稳、专业 |

### English
| Voice ID | Name | Gender | Style |
|----------|------|--------|-------|
| en-US-JennyNeural | Jenny | Female | 自然、友好 |
| en-US-GuyNeural | Guy | Male | 专业、稳重 |
| en-GB-SoniaNeural | Sonia | Female | 英式、优雅 |

## Examples

### Example 1: News Video
```
User: "把这篇新闻生成视频：https://news.example.com/article"

Steps:
1. web_fetch: 获取新闻内容
2. LLM: 生成新闻播报稿件（300字左右）
3. edge-tts: 使用 zh-CN-YunyangNeural 生成音频
4. ffmpeg: 合成视频（背景+字幕）
5. 输出: news_video.mp4
```

### Example 2: Tutorial Video
```
User: "生成教程视频：https://docs.example.com/tutorial"

Steps:
1. web_fetch: 获取教程内容
2. LLM: 生成分步骤解说稿件
3. edge-tts: 使用 zh-CN-XiaoxiaoNeural 生成音频
4. ffmpeg: 合成视频
5. 输出: tutorial_video.mp4
```

### Example 3: Custom Style
```
User: "用幽默风格生成视频：https://blog.example.com/funny-story"

Steps:
1. web_fetch: 获取内容
2. LLM: 用幽默风格改写稿件
3. edge-tts: 使用 zh-CN-XiaoyiNeural（活泼女声）
4. ffmpeg: 合成视频
5. 输出: funny_video.mp4
```

## Advanced Features

### 1. Background Management
```bash
# List available backgrounds
ls ~/.chaobot/workspace/backgrounds/

# Use specific background
chaobot run -m "用科技感背景生成视频：https://..."
```

### 2. Batch Processing
```bash
# Generate multiple videos
for url in url1 url2 url3; do
  chaobot run -m "生成视频：$url"
done
```

### 3. Custom Duration
```
User: "生成30秒短视频：https://..."
User: "生成5分钟长视频：https://..."
```

## Output Location

Generated videos are saved to:
```
~/.chaobot/workspace/videos/
├── 2024-01-15_001.mp4
├── 2024-01-15_002.mp4
└── ...
```

## Troubleshooting

### FFmpeg not found
```bash
# Check installation
ffmpeg -version

# Add to PATH if needed
export PATH=$PATH:/usr/local/bin
```

### TTS fails
```bash
# Check edge-tts installation
pip show edge-tts

# Test basic usage
edge-tts --text "测试" --write-media test.mp3
```

### Video quality issues
```bash
# Higher quality
ffmpeg -i bg.jpg -i audio.mp3 -c:v libx264 -crf 18 -c:a aac -b:a 256k output.mp4

# Lower quality (smaller file)
ffmpeg -i bg.jpg -i audio.mp3 -c:v libx264 -crf 28 -c:a aac -b:a 128k output.mp4
```

## Tips

1. **Script Length**: 150-200 words ≈ 1 minute video
2. **Voice Selection**: Match voice to content style
3. **Background**: Use high-quality images (1920x1080)
4. **Subtitles**: Improve accessibility and engagement
5. **Testing**: Always preview before final export