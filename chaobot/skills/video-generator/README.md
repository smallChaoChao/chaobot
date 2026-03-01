# Video Generator Skill

🎬 从网页 URL 自动生成带字幕的解说视频

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 🌐 网页抓取 | 自动获取网页内容并截图 |
| ✍️ 去AI味写作 | 将内容改写成自然口语风格 |
| 🎤 TTS语音 | Microsoft Edge TTS，多种中文语音 |
| 📝 SRT字幕 | 自动生成时间轴字幕 |
| 🎬 视频合成 | FFmpeg 合成最终视频 |

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装 FFmpeg
brew install ffmpeg

# 安装 Python 依赖
cd /path/to/chaobot
uv add edge-tts pyyaml
```

### 2. 基础用法

```bash
# 在 chaobot 中使用
chaobot run -m "帮我把这个网页生成视频：https://example.com/article"

# 指定风格和语音
chaobot run -m "用新闻风格生成视频，语音用云扬：https://news.com/story"

# 自定义背景
chaobot run -m "用这张图片做背景生成视频：/path/to/bg.jpg，内容来自 https://..."
```

## 📋 完整工作流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Step 1     │    │  Step 2     │    │  Step 3     │    │  Step 4     │    │  Step 5     │
│  获取内容    │ -> │  生成稿件    │ -> │  TTS音频    │ -> │  生成字幕    │ -> │  合成视频    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      │                  │                  │                  │                  │
      v                  v                  v                  v                  v
 browser_navigate    LLM改写           edge-tts           VTT->SRT          ffmpeg
 browser_screenshot  去AI味            生成音频           时间轴字幕         视频合成
 web_fetch           200-400字
```

## 🎨 写作风格配置

### 可用风格

| 风格 | 描述 | 适用场景 |
|------|------|---------|
| `natural` | 自然口语，像朋友聊天 | 教程、解说 |
| `storytelling` | 故事叙述，引人入胜 | 故事、案例 |
| `news` | 新闻播报，专业简洁 | 新闻、资讯 |
| `humorous` | 幽默风趣，轻松搞笑 | 娱乐、段子 |
| `professional` | 专业解读，深度分析 | 商务、知识 |

### 去 AI 味规则

**避免使用：**
- 首先、其次、再次、最后
- 综上所述、总而言之
- 值得注意的是、不可否认
- 显而易见、毋庸置疑

**推荐使用：**
- "说起来有个事儿..."
- "你猜怎么着..."
- "有意思的是..."
- "这事儿告诉我们..."

## 🎤 语音选择

| ID | 名称 | 性别 | 风格 | 适用场景 |
|----|------|------|------|---------|
| `xiaoxiao` | 晓晓 | 女 | 温柔自然 | 教程、解说 |
| `xiaoyi` | 晓伊 | 女 | 活泼可爱 | 轻松内容 |
| `yunxi` | 云希 | 男 | 年轻阳光 | 科技、潮流 |
| `yunyang` | 云扬 | 男 | 新闻播报 | 新闻、正式 |
| `yunjian` | 云健 | 男 | 沉稳专业 | 商务、知识 |

## ⚙️ 配置文件

配置文件位于: `skills/video-generator/config.yaml`

```yaml
# 默认语音
voice:
  default: "xiaoxiao"

# 写作风格
writing_styles:
  default: "natural"

# 背景设置
background:
  mode: "screenshot"  # screenshot, generated, custom

# 视频参数
video:
  resolution: "1920x1080"
  subtitle:
    font: "PingFang SC"
    font_size: 24

# 内容处理
content:
  min_length: 200
  max_length: 800
  ideal_length: 400
```

## 📁 文件结构

```
skills/video-generator/
├── SKILL.md              # Skill 文档（AI 读取）
├── config.yaml           # 配置文件
├── video_generator.py    # 核心功能类
├── README.md             # 使用说明
└── evals/
    └── evals.json        # 测试用例
```

## 📤 输出位置

```
~/.chaobot/workspace/videos/
├── 2024-01-15_001.mp4      # 最终视频
├── 2024-01-15_001.srt      # 字幕文件
├── 2024-01-15_001.mp3      # 音频文件
└── backgrounds/
    └── 2024-01-15_001.png  # 背景图片
```

## 🔧 故障排除

| 问题 | 解决方案 |
|------|---------|
| ffmpeg not found | `brew install ffmpeg` |
| edge-tts 失败 | `uv add edge-tts` |
| 字幕不显示 | 检查 SRT 编码为 UTF-8 |
| 视频质量差 | 调整 CRF 值（18-28，越小越好）|

## 📊 质量提示

1. **稿件长度**: 200-400 字 ≈ 1-2 分钟视频
2. **语音选择**: 根据内容风格匹配语音
3. **背景图片**: 使用 1920x1080 高清图片
4. **字幕样式**: 白字黑边，底部居中
5. **预览测试**: 先生成短视频测试效果