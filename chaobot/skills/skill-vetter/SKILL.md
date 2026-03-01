---
name: skill-vetter
description: "Security and safety checker for agent actions - validates commands before execution"
homepage: https://clawhub.ai
always: true
metadata: {"chaobot":{"emoji":"🛡️","requires":{}}}
---

# Skill Vetter

Security layer that validates agent actions before execution to prevent harmful operations.

## Safety Rules

### File Operations

**ALLOWED:**
- Read/write files in workspace directory
- Create new files and directories
- Edit existing project files
- List directory contents

**BLOCKED:**
- Delete system files (/etc, /usr, etc.)
- Modify system configuration
- Access sensitive files (.ssh, .aws, etc.)
- Write outside workspace without confirmation

### Command Execution

**ALLOWED:**
- Development tools (git, npm, pip, etc.)
- File operations (ls, cat, grep, etc.)
- Build commands (make, cargo, etc.)
- Test runners

**REQUIRES CONFIRMATION:**
- Commands with `sudo` or `su`
- Package installation/removal
- Network operations (curl, wget to external)
- Commands modifying system state

**BLOCKED:**
- `rm -rf /` or similar destructive patterns
- Commands with shell injection risks
- Cryptocurrency miners
- Data exfiltration attempts

### Network Operations

**ALLOWED:**
- Local development servers
- API calls to known services
- Package manager operations

**REQUIRES CONFIRMATION:**
- Outbound connections to unknown hosts
- Large data transfers
- Authentication token transmission

## Validation Process

Before executing any action:

1. **Check intent** - Does the action match the user's request?
2. **Check scope** - Is it limited to the workspace?
3. **Check safety** - Does it follow the rules above?
4. **Check confirmation** - Does it require user approval?

If unsure, ask the user for confirmation before proceeding.

## Examples

**Safe action:**
```
User: "Create a README.md file"
Action: Write file to workspace ✓
```

**Requires confirmation:**
```
User: "Install this package"
Action: Run `pip install unknown-package` → Ask user first
```

**Blocked action:**
```
User: "Delete everything"
Action: `rm -rf /` → BLOCKED - explain why
```
