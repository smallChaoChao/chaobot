# Video Generator Skill 🎬

自动从网页内容生成视频的技能。

## 功能特性

- ✅ 网页内容抓取
- ✅ LLM 智能转写稿件
- ✅ TTS 语音合成（支持中英文）
- ✅ 字幕自动生成
- ✅ 视频合成输出
- ✅ 多种背景支持

## 安装依赖

```bash
# 1. 安装 FFmpeg
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
winget install ffmpeg

# 2. 安装 Edge-TTS
pip install edge-tts

# 3. (可选) 安装 PIL 用于生成背景
pip install Pillow
```

## 快速开始

### 方式一：使用 chaobot 命令

```bash
# 生成视频
chaobot run -m "生成视频：https://example.com/article"

# 指定风格
chaobot run -m "用新闻播报风格生成视频：https://news.site.com/story"

# 指定时长
chaobot run -m "生成30秒短视频：https://..."
```

### 方式二：使用辅助脚本

```bash
# 直接生成 TTS
cd chaobot/skills/video-generator
python video_generator.py "大家好，欢迎观看本期视频"

# 在代码中使用
from video_generator import VideoGenerator
import asyncio

async def main():
    gen = VideoGenerator()
    await gen.generate_tts("测试文本", "output.mp3")

asyncio.run(main())
```

## 工作流程

```
1. 用户请求 → 2. 抓取网页 → 3. LLM转写 → 4. TTS生成 → 5. 视频合成
```

### 详细步骤

1. **网页抓取**
   - 使用 `web_fetch` 工具获取网页内容
   - 提取正文，过滤广告和导航

2. **内容转写**
   - LLM 根据内容生成视频稿件
   - 控制字数（150-200字 ≈ 1分钟）
   - 调整语气风格

3. **TTS 生成**
   - 使用 Microsoft Edge TTS
   - 支持多种中文语音
   - 自动生成字幕

4. **视频合成**
   - FFmpeg 合成视频
   - 添加背景图片/视频
   - 嵌入字幕

## 可用语音

### 中文语音

| 代码 | 名称 | 性别 | 风格 |
|------|------|------|------|
| xiaoxiao | 晓晓 | 女 | 温柔、自然 |
| xiaoyi | 晓伊 | 女 | 活泼、可爱 |
| yunxi | 云希 | 男 | 年轻、阳光 |
| yunyang | 云扬 | 男 | 新闻播报 |
| yunjian | 云健 | 男 | 沉稳、专业 |

### 英文语音

| 代码 | 名称 | 性别 | 风格 |
|------|------|------|------|
| jenny | Jenny | 女 | 自然、友好 |
| guy | Guy | 男 | 专业、稳重 |
| sonia | Sonia | 女 | 英式、优雅 |

## 背景管理

### 添加背景

```bash
# 创建背景目录
mkdir -p ~/.chaobot/workspace/backgrounds

# 添加背景图片/视频
cp my_background.jpg ~/.chaobot/workspace/backgrounds/
cp my_background.mp4 ~/.chaobot/workspace/backgrounds/
```

### 支持的格式

- 图片：`.jpg`, `.jpeg`, `.png`
- 视频：`.mp4`, `.mov`

## 输出位置

生成的视频保存在：
```
~/.chaobot/workspace/videos/
├── 2024-01-15_001.mp4
├── 2024-01-15_002.mp4
└── ...
```

## 示例用法

### 示例 1：新闻视频

```bash
chaobot run -m "把这篇新闻生成视频：https://news.example.com/article"
```

流程：
1. 抓取新闻内容
2. 生成新闻播报稿件（300字）
3. 使用 `yunyang` 语音（新闻播报风格）
4. 合成视频

### 示例 2：教程视频

```bash
chaobot run -m "生成教程视频：https://docs.example.com/tutorial"
```

流程：
1. 抓取教程内容
2. 生成分步骤解说稿件
3. 使用 `xiaoxiao` 语音（温柔风格）
4. 合成视频

### 示例 3：幽默风格

```bash
chaobot run -m "用幽默风格生成视频：https://blog.example.com/funny"
```

流程：
1. 抓取内容
2. 用幽默风格改写
3. 使用 `xiaoyi` 语音（活泼风格）
4. 合成视频

## 高级功能

### 自定义时长

```bash
# 30秒短视频
chaobot run -m "生成30秒短视频：https://..."

# 5分钟长视频
chaobot run -m "生成5分钟长视频：https://..."
```

### 指定背景

```bash
chaobot run -m "用科技感背景生成视频：https://..."
```

### 批量生成

```bash
for url in url1 url2 url3; do
  chaobot run -m "生成视频：$url"
done
```

## 常见问题

### FFmpeg not found

```bash
# 检查安装
ffmpeg -version

# 添加到 PATH
export PATH=$PATH:/usr/local/bin
```

### TTS 失败

```bash
# 检查 edge-tts
pip show edge-tts

# 测试基本用法
edge-tts --text "测试" --write-media test.mp3
```

### 视频质量问题

```bash
# 高质量
ffmpeg -i bg.jpg -i audio.mp3 -c:v libx264 -crf 18 -c:a aac -b:a 256k output.mp4

# 低质量（文件更小）
ffmpeg -i bg.jpg -i audio.mp3 -c:v libx264 -crf 28 -c:a aac -b:a 128k output.mp4
```

## 技巧

1. **稿件长度**：150-200 字 ≈ 1 分钟视频
2. **语音选择**：根据内容风格选择合适的语音
3. **背景质量**：使用 1920x1080 高清图片
4. **字幕**：提高可访问性和参与度
5. **测试**：正式导出前先预览

## 文件结构

```
video-generator/
├── SKILL.md              # Skill 文档
├── README.md             # 使用说明
└── video_generator.py    # 辅助脚本
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License