# 📚 Chaobot Learnings

Continuous improvement through logged experiences.

## Learning Format

```markdown
## [LRN-YYYYMMDD-XXX] Category

**Logged**: ISO-8601 timestamp
**Priority**: low | medium | high | critical
**Status**: pending | resolved | promoted | promoted_to_skill
**Area**: frontend | backend | infra | tests | docs | config | behavior

### Summary
One sentence description

### Details
Full context and explanation

### Suggested Action
Specific fix or improvement

### Metadata
- Source: conversation | error | user_feedback
- Related Files: path/to/file
- Tags: tag1, tag2
- Pattern-Key: category.specific_issue
- Recurrence-Count: 1
```

## Promotion Path

```
Learning (in .learnings/)
    ↓
Is it project-specific?
    ├─ YES → Keep in .learnings/
    └─ NO → Is it about behavior/style?
        ├─ YES → Promote to SOUL.md
        └─ NO → Is it about tool usage?
            ├─ YES → Promote to TOOLS.md
            └─ NO → Promote to AGENTS.md (workflows)
```

## Active Learnings

<!-- New learnings added here -->

## Resolved Learnings

<!-- Moved here after resolution -->

## Promoted Learnings

<!-- Track what was promoted and where -->
