# 🤖 chaobot

一个轻量级、现代化的个人 AI 助手，灵感来源于 [nanobot](https://github.com/HKUDS/nanobot)，采用更先进的架构设计。

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-22%20passed-brightgreen.svg)]()

## ✨ 特性

- 🪶 **轻量级**: 核心代码简洁，易于理解和扩展
- 🔐 **安全**: 多层安全控制，工作区隔离，命令白名单
- ⚡ **高性能**: 全异步架构，支持流式响应
- 🛠️ **可扩展**: 插件化工具系统，易于添加新功能
- 💪 **类型安全**: 完整的类型注解，IDE 友好
- 🎨 **美观**: 使用 Rich 库提供优雅的 CLI 界面
- 🔄 **热重载**: 配置文件修改后自动生效

## 🚀 快速开始

### 1. 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/chaobot.git
cd chaobot

# 使用 uv 安装（推荐）
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# 或使用 pip
pip install -e ".[dev]"
```

### 2. 初始化

```bash
# 初始化配置目录和文件
chaobot init

# 输出示例：
# ✅ chaobot initialized successfully!
# Directory structure:
#   ~/.chaobot/config.json
#   ~/.chaobot/workspace/memory/MEMORY.md
#   ~/.chaobot/workspace/sessions/
```

### 3. 配置 API 密钥

编辑配置文件 `~/.chaobot/config.json`：

```json
{
  "providers": {
    "openai": {
      "enabled": true,
      "api_key": "sk-your-api-key",
      "api_base": "https://api.openai.com/v1"
    }
  },
  "agents": {
    "defaults": {
      "model": "gpt-4",
      "provider": "openai",
      "temperature": 0.7
    }
  }
}
```

**支持的 Provider**:
- OpenAI / Azure OpenAI
- OpenRouter (推荐，支持多种模型)
- Anthropic Claude
- 阿里云 DashScope
- 其他 OpenAI 兼容 API

### 4. 开始使用

```bash
# 单条消息模式
chaobot run -m "你好，请介绍一下自己"

# 交互模式
chaobot run

# 指定会话（对话历史隔离）
chaobot run -s work
chaobot run -s personal

# 查看状态
chaobot status

# 显示帮助
chaobot --help
```

## 📖 使用指南

### 命令行选项

```bash
chaobot run [OPTIONS]

Options:
  -m, --message TEXT      发送单条消息后退出
  -s, --session TEXT      指定会话 ID（默认: default）
  --no-markdown          禁用 Markdown 渲染
  --no-stream            禁用流式响应
  --logs                 显示运行时日志
  --help                 显示帮助信息
```

### 工具使用

chaobot 支持多种工具，AI 会根据需要自动调用：

**Shell 工具**
```
用户: 查看当前目录下的文件
AI: [调用 shell 工具执行 ls -la]
```

**文件工具**
```
用户: 读取 README.md 文件
AI: [调用 file_read 工具读取文件]
```

**Web 搜索**
```
用户: 搜索 Python 最新版本
AI: [调用 web_search 工具搜索]
```

### 会话管理

对话历史会自动保存，使用不同的 session ID 可以隔离对话：

```bash
# 工作相关的对话
chaobot run -s work

# 个人学习对话
chaobot run -s study

# 项目开发对话
chaobot run -s project
```

历史记录保存在 `~/.chaobot/workspace/sessions/<session_id>.jsonl`

### 长期记忆

编辑 `~/.chaobot/workspace/memory/MEMORY.md` 添加长期记忆：

```markdown
## User Information
- 名字: Alice
- 职业: 软件工程师

## Preferences
- 喜欢 Python 编程
- 偏好简洁的回答
```

## 📁 项目结构

```
chaobot/
├── chaobot/              # 源代码
│   ├── agent/           # 🧠 Agent 核心逻辑
│   │   ├── loop.py      #    Agent 循环
│   │   ├── memory.py    #    记忆管理
│   │   ├── runner.py    #    运行器
│   │   └── tools/       #    工具集
│   ├── channels/        # 📱 聊天频道
│   ├── config/          # ⚙️ 配置管理
│   ├── providers/       # 🤖 LLM Provider
│   └── cli.py           #    CLI 入口
├── tests/               # 🧪 单元测试
├── docs/                # 📚 文档
└── README.md
```

用户数据目录：
```
~/.chaobot/
├── config.json          # 配置文件
└── workspace/
    ├── memory/          # 长期记忆
    │   ├── MEMORY.md
    │   └── HISTORY.md
    ├── sessions/        # 对话历史
    └── HEARTBEAT.md     # 心跳监控
```

## 🔧 高级配置

### 安全配置

```json
{
  "tools": {
    "restrict_to_workspace": true,
    "brave_api_key": "optional-for-web-search"
  },
  "security": {
    "confirm_destructive_actions": true,
    "allowed_commands": ["ls", "cat", "grep"],
    "blocked_commands": ["rm", "sudo"]
  }
}
```

### 多 Provider 配置

```json
{
  "providers": {
    "openrouter": {
      "enabled": true,
      "api_key": "sk-or-v1-xxx"
    },
    "openai": {
      "enabled": false,
      "api_key": "sk-xxx"
    }
  },
  "agents": {
    "defaults": {
      "provider": "openrouter",
      "model": "anthropic/claude-3-5-sonnet-20241022"
    }
  }
}
```

## 🛡️ 安全性

- **工作区隔离**: 文件操作限制在配置的工作区内
- **命令白名单**: 可配置允许的 shell 命令
- **危险命令拦截**: 自动拦截 rm -rf / 等危险操作
- **路径遍历防护**: 防止 ../../../etc/passwd 等攻击
- **超时控制**: 命令执行默认 60 秒超时

## 🧪 开发

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_config.py -v
pytest tests/test_tools.py -v
pytest tests/test_memory.py -v
```

### 代码风格

```bash
# 格式化代码
black chaobot/ tests/

# 类型检查
mypy chaobot/

# 代码检查
ruff check chaobot/ tests/
```

## 📚 文档

- [开发计划](DEVELOPMENT_PLAN.md) - 详细的开发路线图
- [优化方案](OPTIMIZATIONS.md) - 相比 nanobot 的改进

## 🤝 贡献

欢迎贡献！请查看 [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) 了解当前开发重点。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**免责声明**: 本项目仅供学习和研究使用。
