# 视频生成 Skill 完整指南

## 📋 概述

我已经为你创建了一个完整的视频生成 Skill，包含以下文件：

```
chaobot/skills/video-generator/
├── SKILL.md              # Skill 文档（AI 会读取这个文件）
├── README.md             # 用户指南
├── video_generator.py    # 视频生成核心类
├── example_workflow.py   # 完整工作流示例
└── test_setup.py         # 环境检测脚本
```

## 🚀 快速开始

### 第一步：安装依赖

```bash
# 1. FFmpeg (已安装 ✅)
# 你的系统已经有 ffmpeg

# 2. 安装 edge-tts (TTS 引擎)
pip3 install edge-tts

# 或者如果你使用 uv
uv pip install edge-tts

# 3. (可选) 安装 Pillow 用于生成背景图片
pip3 install Pillow
```

### 第二步：验证安装

```bash
cd /Users/chaochao/ai/chaobot/chaobot/skills/video-generator
python3 test_setup.py
```

### 第三步：添加背景资源

```bash
# 创建背景目录
mkdir -p ~/.chaobot/workspace/backgrounds

# 添加背景图片或视频
# 支持格式: .jpg, .jpeg, .png, .mp4, .mov
cp your_background.jpg ~/.chaobot/workspace/backgrounds/
```

## 🎬 使用方式

### 方式一：通过 chaobot 命令（推荐）

```bash
# 基本用法
chaobot run -m "生成视频：https://example.com/article"

# 指定风格
chaobot run -m "用新闻播报风格生成视频：https://news.site.com"

# 指定时长
chaobot run -m "生成30秒短视频：https://..."
```

### 方式二：直接使用 Python 脚本

```bash
cd /Users/chaochao/ai/chaobot/chaobot/skills/video-generator

# 测试 TTS
python3 -c "
import asyncio
from video_generator import VideoGenerator

async def test():
    gen = VideoGenerator()
    await gen.generate_tts('你好，这是一个测试', 'test.mp3', 'xiaoxiao')
    print('✅ TTS 测试成功')

asyncio.run(test())
"

# 完整工作流
python3 example_workflow.py https://example.com/article
```

## 📖 工作流程详解

```
用户请求
   ↓
1. 抓取网页内容 (web_fetch)
   ↓
2. LLM 转写稿件 (根据风格调整)
   ↓
3. TTS 生成音频 (edge-tts)
   ↓
4. 生成字幕文件 (.vtt)
   ↓
5. 合成视频 (ffmpeg)
   ↓
输出视频文件
```

## 🎨 可用语音

### 中文语音

| 代码 | 名称 | 性别 | 风格 | 适用场景 |
|------|------|------|------|---------|
| `xiaoxiao` | 晓晓 | 女 | 温柔、自然 | 教程、解说 |
| `xiaoyi` | 晓伊 | 女 | 活泼、可爱 | 轻松内容 |
| `yunxi` | 云希 | 男 | 年轻、阳光 | 科技、潮流 |
| `yunyang` | 云扬 | 男 | 新闻播报 | 新闻、正式 |
| `yunjian` | 云健 | 男 | 沉稳、专业 | 商务、知识 |

### 英文语音

| 代码 | 名称 | 性别 | 风格 |
|------|------|------|------|
| `jenny` | Jenny | 女 | 自然、友好 |
| `guy` | Guy | 男 | 专业、稳重 |
| `sonia` | Sonia | 女 | 英式、优雅 |

## 💡 使用示例

### 示例 1：生成新闻视频

```bash
chaobot run -m "把这篇新闻生成视频：https://news.sina.com.cn/article/123"
```

AI 会：
1. 抓取新闻内容
2. 生成新闻播报风格稿件（使用 yunyang 语音）
3. 创建视频

### 示例 2：生成教程视频

```bash
chaobot run -m "生成教程视频：https://docs.python.org/3/tutorial/"
```

AI 会：
1. 抓取教程内容
2. 生成分步骤解说稿件（使用 xiaoxiao 语音）
3. 创建视频

### 示例 3：自定义风格

```bash
chaobot run -m "用幽默风格生成视频，语音用晓伊：https://blog.example.com/funny"
```

## 🔧 高级配置

### 自定义稿件模板

你可以在 SKILL.md 中找到稿件模板：

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

### 批量生成

```bash
# 创建脚本批量处理
cat > batch_generate.sh << 'EOF'
#!/bin/bash
urls=(
  "https://example.com/article1"
  "https://example.com/article2"
  "https://example.com/article3"
)

for url in "${urls[@]}"; do
  chaobot run -m "生成视频：$url"
done
EOF

chmod +x batch_generate.sh
./batch_generate.sh
```

## 📁 输出位置

生成的视频保存在：
```
~/.chaobot/workspace/videos/
├── 2024-01-15_143022.mp4
├── 2024-01-15_150133.mp4
└── ...
```

## 🐛 常见问题

### Q: edge-tts 安装失败？

```bash
# 尝试使用国内镜像
pip3 install edge-tts -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: FFmpeg 找不到？

```bash
# 检查路径
which ffmpeg
# 输出: /opt/homebrew/bin/ffmpeg

# 如果需要，添加到 PATH
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Q: 生成的视频没有声音？

检查：
1. edge-tts 是否正确安装
2. 音频文件是否生成
3. ffmpeg 命令是否正确

### Q: 视频质量不好？

```python
# 在 video_generator.py 中调整质量参数
# crf 值越小，质量越高
crf_map = {
    "low": 28,     # 低质量，文件小
    "medium": 23,  # 中等质量
    "high": 18     # 高质量，文件大
}
```

## 🎯 下一步

1. **安装 edge-tts**
   ```bash
   pip3 install edge-tts
   ```

2. **测试基本功能**
   ```bash
   edge-tts --text "你好，这是一个测试" --write-media test.mp3
   ```

3. **添加背景资源**
   ```bash
   mkdir -p ~/.chaobot/workspace/backgrounds
   # 添加你喜欢的背景图片
   ```

4. **开始使用**
   ```bash
   chaobot run -m "生成视频：https://example.com/article"
   ```

## 📚 技术细节

### TTS 引擎

使用 Microsoft Edge TTS，优点：
- ✅ 免费
- ✅ 高质量
- ✅ 支持多种语言和语音
- ✅ 自动生成字幕时间轴

### 视频合成

使用 FFmpeg，功能：
- ✅ 图片 + 音频 → 视频
- ✅ 视频 + 音频 → 新视频
- ✅ 添加字幕
- ✅ 调整质量

### 稿件生成

由 LLM 自动完成：
- ✅ 提取关键信息
- ✅ 调整语气风格
- ✅ 控制时长
- ✅ 优化表达

---

需要我帮你测试或进一步优化吗？