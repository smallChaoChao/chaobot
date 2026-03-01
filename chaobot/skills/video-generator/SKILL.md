---
name: video-generator
description: "Generate videos from web articles or text. Invoke when user wants to: create video from URL, convert article to video, make short video with narration and subtitles. Workflow: 1) Create output dir, 2) Fetch web content, 3) Summarize and rewrite as video script (short sentences), 4) Generate audio+subtitles using TTS, 5) Compose final video with black background."
homepage: https://github.com/smallChaoChao/chaobot
metadata:
  chaobot:
    emoji: "🎬"
    requires:
      bins: ["ffmpeg", "edge-tts"]
---

# Video Generator

从网页链接或文本生成带字幕的解说视频。

## 工作流程

### Step 1: 创建输出目录

```bash
# 在 skill 目录下创建 output 文件夹
mkdir -p /Users/chaochao/ai/chaobot/chaobot/skills/video-generator/output

# 检查现有 output 目录数量，确定新序号
ls -d /Users/chaochao/ai/chaobot/chaobot/skills/video-generator/output/output* 2>/dev/null | wc -l

# 创建新的输出目录（例如 output1）
mkdir -p /Users/chaochao/ai/chaobot/chaobot/skills/video-generator/output/output1
```

### Step 2: 获取网页内容

使用 web_search 或 web_fetch 工具获取网页内容：

```bash
# 使用 web_search 搜索文章内容
web_search query="文章标题或URL相关关键词"

# 或使用 web_fetch 直接获取
web_fetch url="https://example.com/article"
```

### Step 3: 生成视频脚本

将网页内容转换为视频脚本，要求：
- **一句话一句话的形式**，每句话简短（15-25字）
- 自然口语化，像和朋友聊天
- 避免 AI 味词汇："首先、其次、最后、综上所述、总而言之"
- 开头吸引人，结尾有互动感
- 总长度控制在 200-400 字（约 1-2 分钟视频）

**脚本示例格式**：
```
说起来有个事儿想跟大家分享！
最近我发现了一个特别有意思的项目。
你猜怎么着？
这玩意儿现在已经拿了 2.8 万颗 Star 了！
它到底是干嘛的呢？
简单说就是用代码做视频。
对，你没听错，写代码就能生成视频！
用的是 React 加 TypeScript。
前端同学上手毫无压力。
你想做个数据可视化动画？
没问题！
批量生成短视频？
小意思！
这事儿告诉我们什么？
技术人的工具箱里，永远缺不了这种提效神器。
你觉得怎么样？
评论区聊聊呗！
```

### Step 4: 生成音频和字幕

使用脚本生成音频和字幕文件：

```bash
# 调用生成脚本
cd /Users/chaochao/ai/chaobot/chaobot/skills/video-generator
python generate_video.py \
  --script "你的脚本内容" \
  --output-dir /Users/chaochao/ai/chaobot/chaobot/skills/video-generator/output/output1 \
  --voice zh-CN-XiaoxiaoNeural
```

**可用语音**：
- `zh-CN-XiaoxiaoNeural` - 晓晓（女，温柔自然，推荐）
- `zh-CN-XiaoyiNeural` - 晓伊（女，活泼可爱）
- `zh-CN-YunxiNeural` - 云希（男，年轻阳光）
- `zh-CN-YunyangNeural` - 云扬（男，新闻播报）
- `zh-CN-YunjianNeural` - 云健（男，沉稳专业）

### Step 5: 合成视频

脚本会自动完成视频合成，输出文件：
- `final_video.mp4` - 最终视频
- `audio.mp3` - 音频文件
- `subtitles.srt` - 字幕文件

## 可用脚本

### generate_video.py

**位置**: `/Users/chaochao/ai/chaobot/chaobot/skills/video-generator/generate_video.py`

**功能**: 完整的视频生成流程
- 生成 TTS 音频
- 生成同步字幕
- 创建黑色背景
- 合成最终视频

**参数**:
- `--script`: 视频脚本内容（必需）
- `--output-dir`: 输出目录（必需）
- `--voice`: 语音类型（可选，默认 zh-CN-XiaoxiaoNeural）
- `--rate`: 语速（可选，默认 +10%）

**使用示例**:
```bash
python generate_video.py \
  --script "说起来有个事儿想跟大家分享！最近我发现..." \
  --output-dir /Users/chaochao/ai/chaobot/chaobot/skills/video-generator/output/output1 \
  --voice zh-CN-XiaoxiaoNeural
```

## 完整示例

### 从网页生成视频

```
用户: 给网页 https://juejin.cn/post/xxx 生成一个视频

执行步骤:
1. mkdir -p /Users/chaochao/ai/chaobot/chaobot/skills/video-generator/output/output1
2. web_search query="掘金文章标题关键词" 或 web_fetch url="https://juejin.cn/post/xxx"
3. LLM 总结内容并生成脚本（一句话一句的格式）
4. python generate_video.py --script "脚本内容" --output-dir /Users/chaochao/ai/chaobot/chaobot/skills/video-generator/output/output1
5. 报告最终视频路径: /Users/chaochao/ai/chaobot/chaobot/skills/video-generator/output/output1/final_video.mp4
```

### 从文本生成视频

```
用户: 把这段文字生成视频：人工智能正在改变...

执行步骤:
1. mkdir -p /Users/chaochao/ai/chaobot/chaobot/skills/video-generator/output/output1
2. LLM 将文本改写为脚本（一句话一句的格式）
3. python generate_video.py --script "脚本内容" --output-dir /Users/chaochao/ai/chaobot/chaobot/skills/video-generator/output/output1
4. 报告最终视频路径
```

## 输出文件结构

```
/Users/chaochao/ai/chaobot/chaobot/skills/video-generator/output/
└── output{N}/
    ├── final_video.mp4    # 最终视频
    ├── audio.mp3          # 音频文件
    └── subtitles.srt      # 字幕文件
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
| 视频没有声音 | 检查 audio.mp3 是否存在 |
