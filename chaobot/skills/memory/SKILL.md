---
name: memory
description: "Long-term memory system for storing and retrieving facts, preferences, and important information"
homepage: https://github.com/HKUDS/nanobot
always: true
metadata: {"chaobot":{"emoji":"🧠","requires":{}}}
---

# Memory Skill

Store and retrieve long-term information across conversations. The memory system helps you remember important facts, user preferences, and key details.

## How It Works

The memory system has two layers:

1. **MEMORY.md** - Long-term facts and preferences
2. **HISTORY.md** - Conversation history and context

## Memory Operations

### Store Information

When you learn something important about the user or context, store it:

```
Remember: User prefers Python over JavaScript
Remember: User works at Company XYZ as a developer
Remember: User is allergic to peanuts
```

### Retrieve Information

Access stored memories to personalize responses:

```
Recall: What does the user do for work?
Recall: What are user's technical preferences?
```

### Update Memory

Update existing information when it changes:

```
Update: User now works at Company ABC (was XYZ)
```

## What to Remember

**Important facts:**
- User's name, role, company
- Technical preferences (languages, frameworks)
- Project details and goals
- Important dates or deadlines

**Preferences:**
- Communication style (formal/casual)
- Response format preferences
- Tool preferences

**Context:**
- Current project context
- Previous conversation topics
- Decisions made

## Memory Format

Store memories in a structured format:

```markdown
## User Profile
- Name: [name]
- Role: [role]
- Company: [company]

## Preferences
- Language: [preferred language]
- Framework: [preferred framework]

## Current Project
- Name: [project name]
- Status: [status]
- Goals: [goals]
```

## Best Practices

1. **Be specific** - Store concrete facts, not vague impressions
2. **Update regularly** - Keep information current
3. **Respect privacy** - Don't store sensitive personal information
4. **Use categories** - Organize memories logically
5. **Summarize** - Keep memories concise and searchable

## Examples

**Store user info:**
```
User mentioned they are a senior Python developer at Google working on cloud infrastructure.
→ Store: Role=Senior Python Dev, Company=Google, Team=Cloud Infrastructure
```

**Store preferences:**
```
User asked for concise responses without fluff.
→ Store: Preference=Concise responses
```

**Store project context:**
```
User is building a chatbot with FastAPI and wants to add WebSocket support.
→ Store: Project=Chatbot, Stack=FastAPI, Goal=Add WebSocket
```

## Memory Commands

When interacting with the user, you can:

- **Remember** - Store new information
- **Recall** - Retrieve stored information
- **Update** - Modify existing memories
- **Forget** - Remove outdated information (rarely needed)

Always check memory before making assumptions about the user's preferences or context.
