# 🤖 chaobot

一个轻量级、现代化的个人 AI 助手，灵感来源于 [nanobot](https://github.com/HKUDS/nanobot)，采用更先进的架构设计。

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-22%20passed-brightgreen.svg)]()

## ✨ 特性

- 🪶 **轻量级**: 核心代码简洁，易于理解和扩展
- 🔐 **安全**: 多层安全控制，工作区隔离，命令白名单
- ⚡ **高性能**: 全异步架构，支持流式响应
- 🛠️ **可扩展**: 插件化工具系统 + Skill 技能系统，易于添加新功能
- 🎨 **美观**: 使用 Rich 库提供优雅的 CLI 界面，带工具调用进度展示
- 🖥️ **可视化配置**: 内置 Dashboard 配置界面，无需手动编辑 JSON
- 🧠 **智能**: Skill 系统让 AI 自主学习新能力
- 💪 **类型安全**: 完整的类型注解，IDE 友好
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

### 3. 配置 API 密钥（两种方式）

#### 方式一：使用 Dashboard 可视化界面（推荐）

```bash
# 启动配置界面，自动打开浏览器
chaobot config

# 或者指定端口
chaobot config --port 8888

# 不自动打开浏览器
chaobot config --no-browser
```

在 Dashboard 中你可以：
- 🎯 切换 AI 模型（支持 OpenAI、Claude、Qwen、DeepSeek 等）
- 🔌 配置多个 Provider
- 📱 设置消息频道（飞书、Telegram、Discord）
- 🛡️ 配置安全选项
- 📝 直接编辑 JSON 配置

#### 方式二：手动编辑配置文件

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
- 阿里云 DashScope (Qwen 系列)
- DeepSeek
- Groq
- Google Gemini
- 其他 OpenAI 兼容 API

**支持的模型示例**:
- `anthropic/claude-3-5-sonnet-20241022` (推荐)
- `openai/gpt-4o`
- `qwen-max` / `qwen3.5-plus` (阿里云)
- `deepseek-chat`
- `llama-3.1-70b-versatile`

### 4. 开始使用

```bash
# 单条消息模式
chaobot run -m "你好，请介绍一下自己"

# 交互模式
chaobot run

# 指定会话（对话历史隔离）
chaobot run -s work
chaobot run -s personal

# 显示详细工具调用日志
chaobot run --logs

# 查看状态
chaobot status

# 显示帮助
chaobot --help
```

### Session 会话管理

不同会话的对话历史完全隔离，适合区分工作、个人等不同场景：

```bash
# 启动 Session 管理 Web 界面（默认命令）
chaobot session

# 指定端口启动
chaobot session --port 8080

# 列出所有会话
chaobot session list

# 清除指定会话的历史
chaobot session clear work

# 清除所有会话
chaobot session clear --all
```

**使用场景示例**:
```bash
# 工作会话 - 技术问题
chaobot run -s work

# 个人会话 - 生活咨询  
chaobot run -s personal

# 项目会话 - 特定项目
chaobot run -s project-name
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
  --logs                 显示运行时日志和工具调用进度
  --help                 显示帮助信息
```

### Skill 技能系统

chaobot 采用 **Skill 系统** 扩展 AI 能力。Skills 是 Markdown 格式的文档，教 AI 如何使用工具完成特定任务。

**工作原理**:
1. 用户提问时，AI 查看可用的 Skills 列表
2. 如果有相关 Skill，AI 会读取 SKILL.md 学习如何使用
3. AI 使用核心 Tools 执行 Skill 中的步骤
4. 返回结果给用户

**已安装的 Skills**:
- 🌤️ **weather** - 查询天气（使用 wttr.in）
- 🔍 **tavily-search** - AI 搜索引擎（需要 API Key）
- 🐙 **github** - GitHub CLI 操作（需要 gh）
- 🧠 **memory** - 长期记忆管理
- 📋 **summarize** - 内容摘要
- 🛡️ **skill-vetter** - Skill 安全检查

**示例**:
```
用户: 杭州天气如何
AI: [读取 weather skill] → [调用 shell 执行 curl] → 杭州今天 13°C，多云
```

### 工具使用

chaobot 核心提供基础 Tools，Skills 使用这些 Tools 完成复杂任务：

**核心 Tools**:
- `shell` - 执行 shell 命令
- `file_read` / `file_write` / `file_edit` - 文件操作
- `web_search` / `web_fetch` - 网络搜索和获取

**工具调用日志**（使用 `--logs` 开启）:
```bash
$ chaobot run --logs
You: 杭州今天多少度
Iteration 1/50
  ↳ tool[file_read] -> path=/Users/.../weather/SKILL.md
Iteration 2/50
  ↳ skill[weather](shell) -> command=curl -s "wttr.in/Hangzhou?format=3"
Iteration 3/50
chaobot:
杭州今天天气：🌦️ +14°C，湿度94%...
```

**日志格式说明**:
- `skill[skill_name](tool_name) -> params` - Skill 调用，显示参数
- `tool[tool_name] -> params` - 普通工具调用
- 参数自动截断，保持输出整洁

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
│   │   ├── context.py   #    上下文构建（含 Skills 提示）
│   │   └── tools/       #    核心工具集
│   ├── channels/        # 📱 聊天频道
│   ├── config/          # ⚙️ 配置管理
│   ├── dashboard/       # 🖥️ 可视化配置界面
│   ├── providers/       # 🤖 LLM Provider
│   ├── skills/          # 📝 Skill 技能文档
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

### Dashboard 配置界面

chaobot 提供两个 Web 管理界面：

#### 1. Config 配置界面

可视化配置 AI 模型、API 密钥、消息频道等：

```bash
# 启动配置界面
chaobot config

# 选项
--host TEXT     绑定地址（默认: 127.0.0.1）
--port INTEGER  端口（默认: 8080）
--no-browser    不自动打开浏览器
```

**界面特性**：
- 🎨 现代化深色主题设计
- 🔔 操作反馈提示（Toast 通知）
- ⏳ 按钮加载状态
- 📱 响应式布局支持移动端

#### 2. Session 会话管理界面

可视化管理和查看对话历史：

```bash
# 启动会话管理界面（默认命令）
chaobot session

# 选项
--host TEXT     绑定地址（默认: 127.0.0.1）
--port INTEGER  端口（默认: 5000）
```

**界面特性**：
- 📊 会话统计概览
- 🔍 会话搜索功能
- 💬 消息查看和编辑
- 🔔 操作反馈提示（Toast 通知）
- 🎨 与 Config 界面一致的深色主题

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

### 模型切换示例

当某个模型额度用完时，快速切换到其他模型：

```bash
# 方式一：使用 Dashboard
chaobot config
# 在界面中选择新的模型，保存即可

# 方式二：手动编辑
# 修改 ~/.chaobot/config.json 中的 model 字段
# 例如从 qwen-max 切换到 qwen3.5-plus
```

## 🛡️ 安全性

- **工作区隔离**: 文件操作限制在配置的工作区内
- **命令白名单**: 可配置允许的 shell 命令
- **危险命令拦截**: 自动拦截 rm -rf / 等危险操作
- **路径遍历防护**: 防止 ../../../etc/passwd 等攻击
- **超时控制**: 命令执行默认 60 秒超时
- **Skill 安全检查**: 自动验证 Skill 的安全性

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
