# 🛠️ Chaobot Tools

Tool capabilities, usage patterns, and integration gotchas.

## Tool Overview

| Tool | Purpose | Common Use Cases |
|------|---------|------------------|
| `shell` | Execute shell commands | Build, deploy, system operations |
| `file_read` | Read file contents | Code review, configuration, logs |
| `file_write` | Create new files | Generate code, configs, documentation |
| `file_edit` | Modify existing files | Refactoring, updates, fixes |
| `web_search` | Search the web | Research, current info, troubleshooting |
| `web_fetch` | Fetch page content | Documentation, articles, data extraction |
| `browser_navigate` | Open web pages | Interactive web tasks |
| `browser_click` | Click page elements | Form submission, navigation |
| `browser_input` | Fill form fields | Data entry, search queries |
| `browser_screenshot` | Capture page images | Visual verification, documentation |
| `browser_get_html` | Extract page HTML | Scraping, analysis |
| `browser_scroll` | Scroll pages | Long content, lazy loading |
| `browser_find_element` | Locate elements | Automation, verification |

## Tool-Specific Guidelines

### Shell Tool

**Security Considerations:**
- Dangerous commands require confirmation (rm -rf, mkfs, etc.)
- Sudo commands prompt for approval
- Workspace restrictions apply
- Command output truncated at 10KB

**Best Practices:**
```bash
# Check before destructive operations
ls -la target_directory
rm -rf target_directory  # Will prompt for confirmation

# Capture both stdout and stderr
command 2>&1 | tee output.log

# Use absolute paths when possible
cd /absolute/path && command
```

**Common Patterns:**
```bash
# Find files
find . -name "*.py" -type f

# Search content
grep -r "pattern" --include="*.py" .

# Process JSON
jq '.key' file.json

# Check disk space
df -h
```

### File Tools

**Read Tool:**
- Use `offset` and `limit` for large files
- Default limit: 2000 lines
- Binary files rejected

**Write Tool:**
- Creates parent directories automatically
- Overwrites existing files (be careful!)
- Respects workspace boundaries

**Edit Tool:**
- Uses search/replace pattern
- Requires exact match
- Fails if pattern not found

**Best Practices:**
```python
# Always read before write
file_read(path="/path/to/file")

# Check if file exists first
shell(command="test -f /path/to/file && echo 'exists'")

# Use offset/limit for large files
file_read(path="large.log", offset=1, limit=100)
```

### Web Tools

**Search Tool:**
- Uses Brave Search API
- Returns top 10 results
- Respects robots.txt

**Fetch Tool:**
- Follows redirects (max 5)
- 30 second timeout
- Returns markdown-converted content

**Best Practices:**
```python
# Search for specific information
web_search(query="python asyncio best practices 2024")

# Fetch documentation
web_fetch(url="https://docs.python.org/3/library/asyncio.html")

# Combine search + fetch
results = web_search(query="error message")
for result in results[:3]:
    web_fetch(url=result["url"])
```

### Browser Tools

**Session Management:**
- Sessions are isolated per user
- Cookies persist within session
- Headless mode by default

**Best Practices:**
```python
# Navigate and wait for load
browser_navigate(url="https://example.com")

# Take screenshot for verification
browser_screenshot(full_page=True)

# Find elements before interacting
elements = browser_find_element(selector=".button")
if elements:
    browser_click(selector=".button")
```

**Common Workflows:**
```python
# Login workflow
browser_navigate(url="https://site.com/login")
browser_input(selector="#username", text="user")
browser_input(selector="#password", text="pass", submit=True)

# Data extraction
browser_navigate(url="https://site.com/data")
browser_scroll(direction="down", amount=1000)
html = browser_get_html()
# Parse HTML for data
```

## Integration Gotchas

### Shell Command Timeouts
- Commands timeout after 60 seconds
- For long operations, use background processes
- Check process status separately

### File Path Handling
- Always use absolute paths
- Workspace root: `~/.chaobot/workspace/`
- Relative paths resolved from workspace

### Web Rate Limiting
- Search: 100 requests/day (free tier)
- Fetch: No explicit limit but be reasonable
- Browser: Share rate limits with fetch

### Browser Resource Usage
- Each session uses ~100MB RAM
- Close sessions when done
- Max 5 concurrent sessions recommended

## Error Handling

### Common Errors & Solutions

**Shell: "Permission denied"**
```bash
# Check permissions
ls -la file
# Fix with chmod if needed
chmod +x script.sh
```

**File: "File not found"**
```python
# Verify path
shell(command="ls -la /path/to/")
# Create directory if needed
shell(command="mkdir -p /path/to/dir")
```

**Web: "Timeout"**
```python
# Retry with shorter content
web_fetch(url="...", max_length=5000)
# Or use browser for dynamic content
```

**Browser: "Element not found"**
```python
# Wait for page load
browser_navigate(url="...")
# Scroll to element
browser_scroll(direction="to", selector="#element")
# Try alternative selectors
browser_find_element(selector="[data-testid='button']")
```

## Performance Tips

### Optimize Shell Commands
```bash
# Use grep before processing
grep "pattern" large.log | head -100

# Avoid unnecessary cat
grep "pattern" file  # Better than: cat file | grep pattern

# Use parallel processing when possible
find . -name "*.py" -exec grep -l "pattern" {} \;
```

### Efficient File Operations
```python
# Read specific sections
file_read(path="file", offset=100, limit=50)

# Batch operations
# Instead of multiple reads, read once and process
content = file_read(path="config.json")
data = json.loads(content)
```

### Web Optimization
```python
# Cache results when possible
# Use fetch instead of browser for static content
# Combine multiple searches into one
```

## Security Reminders

- Never log API keys or passwords
- Validate user input before shell execution
- Be cautious with `rm`, `chmod`, `chown`
- Check URLs before fetching
- Respect robots.txt and terms of service
