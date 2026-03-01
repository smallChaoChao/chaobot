---
name: github
description: "Interact with GitHub using the gh CLI for repositories, PRs, issues, and more"
homepage: https://cli.github.com
metadata: {"chaobot":{"emoji":"🐙","requires":{"bins":["gh"],"env":["GITHUB_TOKEN"]}}}
---

# GitHub Skill

Interact with GitHub repositories, pull requests, issues, and more using the official GitHub CLI (`gh`).

## Setup

Install GitHub CLI:
```bash
# macOS
brew install gh

# Login
gh auth login
```

Or set token directly:
```bash
export GITHUB_TOKEN="ghp_..."
```

## Authentication

Most commands require authentication. Use `gh auth login` or set `GITHUB_TOKEN`.

## Repository Operations

### Clone Repository
```bash
gh repo clone owner/repo
```

### Create Repository
```bash
# Create public repo
gh repo create my-project --public

# Create private repo with description
gh repo create my-project --private --description "My awesome project"
```

### View Repository
```bash
gh repo view owner/repo
gh repo view --web  # Open in browser
```

## Pull Requests

### List PRs
```bash
gh pr list
gh pr list --state merged
gh pr list --author username
```

### View PR
```bash
gh pr view 123
gh pr view 123 --web
```

### Create PR
```bash
gh pr create --title "Fix bug" --body "Description of changes"
```

### Checkout PR
```bash
gh pr checkout 123
```

### Check PR Status
```bash
gh pr checks 123
```

## Issues

### List Issues
```bash
gh issue list
gh issue list --label bug
gh issue list --state closed
```

### View Issue
```bash
gh issue view 456
```

### Create Issue
```bash
gh issue create --title "Bug report" --body "Description"
```

## Workflows (CI/CD)

### List Workflows
```bash
gh workflow list
```

### Run Workflow
```bash
gh workflow run ci.yml
```

### View Workflow Runs
```bash
gh run list
gh run view 1234567890
```

## Releases

### List Releases
```bash
gh release list
```

### Create Release
```bash
gh release create v1.0.0 --title "Version 1.0.0" --notes "Release notes"
```

## Gists

### List Gists
```bash
gh gist list
```

### Create Gist
```bash
gh gist create file.txt --public
```

## Tips

- Always specify `--repo owner/repo` when not in a git directory
- Use `--web` flag to open results in browser
- Many commands support JSON output with `--json` flag

## Examples

**Check PR status:**
```bash
gh pr checks 55 --repo microsoft/vscode
```

**Create issue with labels:**
```bash
gh issue create --title "Feature request" --label enhancement --repo owner/repo
```

**View recent workflow runs:**
```bash
gh run list --repo facebook/react --limit 10
```
