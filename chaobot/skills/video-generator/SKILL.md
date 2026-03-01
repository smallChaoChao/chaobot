---
name: video-generator
description: "Generate videos from web URLs. Use this skill when user wants to: create video from webpage, convert article to video, make video from URL, generate video with narration. Steps: 1) Fetch web content, 2) Summarize and humanize text, 3) Capture screenshot or generate background image, 4) Generate TTS audio with SRT subtitles, 5) Compose final video. Supports configurable writing styles, multiple voices, and custom backgrounds."
homepage: https://github.com/smallChaoChao/chaobot
metadata:
  chaobot:
    emoji: "🎬"
    requires:
      bins: ["ffmpeg", "edge-tts"]
---

# Video Generator Skill

从网页 URL 自动生成带字幕的解说视频。

## 工作流程

当用户请求生成视频时，按以下步骤执行：

### Step 1: 获取网页内容

```
使用 browser_navigate 导航到 URL
使用 browser_screenshot 截取网页截图（作为背景）
使用 browser_get_html 或 web_fetch 获取内容
```

**截图设置：**
- 使用 `full_page: false` 获取可视区域截图
- 截图保存为背景图片

### Step 2: 总结内容并生成稿件

**关键：去 AI 味写作**

使用 LLM 将内容总结为自然口语风格的稿件：

```
你是一位视频内容创作者，擅长用自然、口语化的方式讲述内容。

要求：
1. 像和朋友聊天一样，轻松自然
2. 避免使用"首先、其次、最后、综上所述"等 AI 味词汇
3. 用故事化的方式串联内容
4. 保持 200-400 字的精炼长度
5. 开头要吸引人，结尾要有互动感

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
```

### Step 3: 生成背景图片

**方式一：网页截图（推荐）**
```
browser_screenshot → 保存为 background.png
```

**方式二：纯色背景**
```
ffmpeg -f lavfi -i color=c=#1a1a2e:s=1920x1080:d=60 -frames:v 1 background.png
```

**方式三：自定义背景**
```
使用 ~/.chaobot/workspace/backgrounds/ 目录下的图片
```

### Step 4: TTS 生成音频和字幕

```bash
# 生成音频和字幕
edge-tts --text "你的稿件内容" \
         --voice zh-CN-XiaoxiaoNeural \
         --write-media audio.mp3 \
         --write-subtitles subtitles.vtt

# 转换 VTT 为 SRT 格式
ffmpeg -i subtitles.vtt subtitles.srt
```

**可用语音：**

| ID | 名称 | 性别 | 风格 | 适用场景 |
|----|------|------|------|---------|
| xiaoxiao | 晓晓 | 女 | 温柔自然 | 教程、解说 |
| xiaoyi | 晓伊 | 女 | 活泼可爱 | 轻松内容 |
| yunxi | 云希 | 男 | 年轻阳光 | 科技、潮流 |
| yunyang | 云扬 | 男 | 新闻播报 | 新闻、正式 |
| yunjian | 云健 | 男 | 沉稳专业 | 商务、知识 |

### Step 5: 合成最终视频

```bash
# 合成视频（背景图 + 音频）
ffmpeg -loop 1 -i background.png -i audio.mp3 \
       -c:v libx264 -tune stillimage -c:a aac -b:a 192k \
       -pix_fmt yuv420p -shortest video_no_sub.mp4

# 添加字幕
ffmpeg -i video_no_sub.mp4 \
       -vf "subtitles=subtitles.srt:force_style='FontName=PingFang SC,FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2,MarginV=50'" \
       -c:a copy output.mp4
```

## 配置文件

配置文件位于: `skills/video-generator/config.yaml`

可配置项：
- **voice**: 默认语音、语速
- **writing_styles**: 写作风格模板
- **background**: 背景模式、截图设置
- **video**: 分辨率、字幕样式、视频质量
- **content**: 稿件长度、段落设置

## 使用示例

### 示例 1: 基础用法
```
用户: 帮我把这个网页生成视频：https://example.com/article

执行流程:
1. browser_navigate → https://example.com/article
2. browser_screenshot → background.png
3. web_fetch → 获取内容
4. LLM → 生成自然口语稿件
5. edge-tts → audio.mp3 + subtitles.srt
6. ffmpeg → output.mp4
```

### 示例 2: 指定风格和语音
```
用户: 用新闻风格生成视频，语音用云扬：https://news.com/story

配置:
- writing_style: news
- voice: yunyang
```

### 示例 3: 自定义背景
```
用户: 用这张图片做背景生成视频：/path/to/image.jpg，内容来自 https://...

步骤:
1. 跳过截图步骤
2. 使用指定图片作为背景
3. 继续后续流程
```

## 输出位置

生成的文件保存在 `~/.chaobot/workspace/videos/`:
```
videos/
├── 2024-01-15_001.mp4      # 最终视频
├── 2024-01-15_001.srt      # 字幕文件
├── 2024-01-15_001.mp3      # 音频文件
└── backgrounds/
    └── 2024-01-15_001.png  # 背景图片
```

## 环境要求

```bash
# 检查安装
ffmpeg -version
edge-tts --version

# 安装命令
brew install ffmpeg          # macOS
pip install edge-tts         # Python TTS
```

## 故障排除

| 问题 | 解决方案 |
|------|---------|
| ffmpeg not found | `brew install ffmpeg` |
| edge-tts 失败 | `pip install edge-tts --upgrade` |
| 字幕不显示 | 检查 SRT 编码为 UTF-8 |
| 视频质量差 | 调整 CRF 值（18-28，越小越好）|

## 质量提示

1. **稿件长度**: 200-400 字 ≈ 1-2 分钟视频
2. **语音选择**: 根据内容风格匹配语音
3. **背景图片**: 使用 1920x1080 高清图片
4. **字幕样式**: 白字黑边，底部居中
5. **预览测试**: 先生成短视频测试效果