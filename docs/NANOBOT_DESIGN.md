# nanobot 设计参考文档

> 本文档记录 nanobot 项目的关键设计思路，供 chaobot 开发参考

## 1. 项目结构

```
nanobot/
├── nanobot/
│   ├── agent/           # Agent核心逻辑
│   │   ├── loop.py      # Agent主循环
│   │   ├── context.py   # 上下文构建
│   │   ├── memory.py    # 记忆管理
│   │   ├── subagent.py  # 子代理管理
│   │   └── tools/       # 工具实现
│   ├── bus/             # 消息总线
│   │   ├── events.py    # 消息事件定义
│   │   └── queue.py     # 消息队列
│   ├── channels/        # 聊天频道
│   │   ├── base.py      # 频道基类
│   │   ├── manager.py   # 频道管理器
│   │   └── feishu.py    # 飞书实现
│   ├── config/          # 配置管理
│   ├── providers/       # LLM提供商
│   ├── session/         # 会话管理
│   ├── cron/            # 定时任务
│   ├── heartbeat/       # 心跳服务
│   └── cli/             # 命令行接口
```

## 2. 核心设计原则

### 2.1 消息总线 (Message Bus)

**位置**: `bus/queue.py`

**设计**:
```python
class MessageBus:
    def __init__(self):
        self.inbound: asyncio.Queue[InboundMessage] = asyncio.Queue()
        self.outbound: asyncio.Queue[OutboundMessage] = asyncio.Queue()
```

**关键点**:
- 使用 `asyncio.Queue` 实现异步消息队列
- 两个独立队列：inbound（频道→Agent）、outbound（Agent→频道）
- 生产-消费模式，解耦频道和Agent

**消息类型**:
```python
@dataclass
class InboundMessage:
    channel: str           # 频道类型
    sender_id: str         # 发送者ID
    chat_id: str           # 聊天ID
    content: str           # 内容
    media: list[str]       # 媒体文件
    metadata: dict         # 元数据

@dataclass
class OutboundMessage:
    channel: str
    chat_id: str
    content: str
    media: list[str]
    reply_to: str | None
```

### 2.2 Agent 主循环

**位置**: `agent/loop.py`

**设计**:
- 单循环处理所有消息
- 从 MessageBus 消费 inbound 消息
- 调用 LLM，执行工具，发送 outbound 消息

**流程**:
```
while running:
    msg = await bus.inbound.get()
    response = await process_with_llm(msg)
    await bus.outbound.put(response)
```

### 2.3 频道基类

**位置**: `channels/base.py`

**设计**:
```python
class BaseChannel(ABC):
    @abstractmethod
    async def start(self) -> None: ...
    
    @abstractmethod
    async def stop(self) -> None: ...
    
    @abstractmethod
    async def send(self, msg: OutboundMessage) -> None: ...
    
    async def _handle_message(self, ...):
        # 权限检查
        if not self.is_allowed(sender_id):
            return
        # 发布到总线
        await self.bus.inbound.put(msg)
```

### 2.4 频道管理器

**位置**: `channels/manager.py`

**职责**:
- 管理所有启用的频道
- 启动/停止所有频道
- 分发 outbound 消息到对应频道

```python
class ChannelManager:
    async def _dispatch_outbound(self):
        while True:
            msg = await self.bus.outbound.get()
            channel = self.channels.get(msg.channel)
            if channel:
                await channel.send(msg)
```

## 3. 关键设计差异

### 3.1 chaobot 当前设计 vs nanobot

| 方面 | nanobot | chaobot (当前) |
|------|---------|----------------|
| 消息总线 | `asyncio.Queue` | Handler注册模式 |
| Agent位置 | `agent/loop.py` | `core/agent.py` |
| 消息处理 | 集中式循环 | 分布式Handler |
| 频道管理 | ChannelManager | 直接集成在Server |

### 3.2 推荐改进方向

1. **消息总线**: 使用 `asyncio.Queue` 替代 Handler 模式，更简单清晰
2. **Agent位置**: 将 MessageAgent 移回 `agent/` 目录
3. **目录结构**: 移除 `core/` 目录，按功能分散到各模块
4. **频道管理**: 添加 ChannelManager 统一管理频道

## 4. 子代理 (Subagent)

**位置**: `agent/subagent.py`

**功能**: 后台任务执行系统

**使用场景**:
- 长时间运行的代码分析
- 批量文件处理
- 耗时的网络搜索

**工作流程**:
1. Agent 调用 `spawn` 工具启动子代理
2. 子代理在后台独立执行
3. 完成后通过 `system` 频道通知主Agent
4. 主Agent总结结果给用户

## 5. 记忆系统

**位置**: `agent/memory.py`

**双层记忆**:
- **MEMORY.md**: 长期事实记忆
- **HISTORY.md**: 可搜索的历史日志

**自动整合**:
- 定期将旧消息归档
- 提取关键信息到 MEMORY.md

## 6. 工具系统

**位置**: `agent/tools/`

**设计**:
```python
class Tool(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @property
    @abstractmethod
    def description(self) -> str: ...
    
    @abstractmethod
    async def execute(self, **kwargs) -> str: ...
```

**工具注册**:
- ToolRegistry 动态管理工具
- 支持 MCP 工具动态加载

## 7. 配置系统

**位置**: `config/schema.py`

**特点**:
- Pydantic 模型验证
- 支持环境变量覆盖
- 嵌套配置结构

## 8. 参考代码片段

### 8.1 消息总线使用

```python
# 初始化
bus = MessageBus()

# 频道发布消息
await bus.inbound.put(InboundMessage(...))

# Agent消费消息
msg = await bus.inbound.get()

# Agent发布回复
await bus.outbound.put(OutboundMessage(...))

# 频道管理器分发
msg = await bus.outbound.get()
await channel.send(msg)
```

### 8.2 频道实现模板

```python
class MyChannel(BaseChannel):
    name = "mychannel"
    
    async def start(self):
        # 启动连接
        pass
    
    async def stop(self):
        # 停止连接
        pass
    
    async def send(self, msg: OutboundMessage):
        # 发送消息到平台
        pass
    
    async def _on_message(self, data):
        # 收到消息时
        await self._handle_message(...)
```

## 9. 开发建议

1. **保持简单**: nanobot 核心只有 ~4,000 行代码
2. **模块化**: 每个功能独立模块，清晰接口
3. **异步优先**: 使用 asyncio 处理所有 IO
4. **类型安全**: 完整的类型注解
5. **配置驱动**: 通过配置启用/禁用功能

---

*最后更新: 2026-03-01*
