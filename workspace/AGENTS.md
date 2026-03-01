# 🤖 Chaobot Agents

Multi-agent workflows, delegation patterns, and automation rules.

## Agent Types

### 1. Main Agent (You)
The primary agent handling user interactions. Responsible for:
- Understanding user intent
- Coordinating with specialized agents
- Maintaining session context
- Presenting results to user

### 2. Subagent System
Background task execution for long-running operations.

**When to Spawn Subagents:**
- Code analysis across multiple files
- Batch file processing
- Deep web research
- Long-running data processing
- Independent evaluations

**Subagent Communication:**
- Spawn with `spawn` tool
- Receive completion via callback
- Results aggregated by main agent
- Use `subagent_wait` to block for results

## Workflow Patterns

### Pattern 1: Sequential Execution
```
User Request → Plan Steps → Execute Step 1 → Execute Step 2 → ... → Present Result
```

**Use when:** Tasks have clear dependencies
**Example:** Create skill → Write SKILL.md → Create test cases → Run evaluation

### Pattern 2: Parallel Delegation
```
User Request → Spawn N Subagents → Collect Results → Aggregate → Present
```

**Use when:** Multiple independent tasks
**Example:** Analyze 5 files simultaneously, Search multiple sources

### Pattern 3: Iterative Refinement
```
Draft → Evaluate → Identify Issues → Refine → Re-evaluate → ... → Final
```

**Use when:** Quality-critical outputs
**Example:** Skill development, Documentation writing, Complex code generation

## Delegation Rules

### DO Delegate When:
- Task takes >30 seconds
- Independent of current context
- Can be verified objectively
- User explicitly asks for background processing

### DON'T Delegate When:
- Requires continuous user interaction
- Needs immediate feedback
- Context-dependent decisions required
- Simple/quick task

## Session Management

### Session Isolation
- Each conversation has unique session_id
- History isolated per session
- Skills can access session context
- Subagents inherit parent session

### Cross-Session Communication
- Use memory skill for persistence
- Store learnings in .learnings/
- Reference previous sessions via memory

## Automation Rules

### Cron Tasks
```
Schedule → Condition → Action → Notify
```

**Examples:**
- Daily news summary at 9am
- Weekly code quality report
- Periodic health checks

### Event Hooks
```
Trigger → Condition → Handler → Response
```

**Available Hooks:**
- `on_tool_error` - Log and analyze failures
- `on_skill_complete` - Track usage patterns
- `on_session_start` - Load relevant context

## Best Practices

### 1. Clear Task Definition
When spawning subagents:
- Specific objective
- Expected output format
- Success criteria
- Time limit (if applicable)

### 2. Result Aggregation
When collecting subagent results:
- Compare outputs if multiple agents
- Identify conflicts
- Summarize key findings
- Present in structured format

### 3. Error Handling
- Subagent failures don't crash main agent
- Retry with modified approach
- Fallback to alternative method
- Inform user of issues

### 4. Progress Tracking
For long operations:
- Show progress indicators
- Update user periodically
- Allow cancellation
- Preserve partial results

## Tool Usage Patterns

### File Operations
```
Read → Analyze → Modify → Verify
```

### Shell Commands
```
Check → Execute → Capture → Parse
```

### Web Operations
```
Search → Fetch → Extract → Summarize
```

### Browser Automation
```
Navigate → Interact → Extract → Close
```

## Quality Gates

Before completing tasks:
- [ ] Requirements met
- [ ] No obvious errors
- [ ] Output format correct
- [ ] User can take next action

Before delegating:
- [ ] Task clearly defined
- [ ] Subagent has necessary context
- [ ] Callback mechanism configured
- [ ] Fallback plan ready
