# ❌ Error Log

Track errors and their resolutions for pattern analysis.

## Error Format

```markdown
## [ERR-YYYYMMDD-XXX] Error Type

**Occurred**: ISO-8601 timestamp
**Tool**: tool_name (if applicable)
**Severity**: warning | error | critical
**Status**: investigating | fixed | workaround | wontfix

### Error Message
```
Full error message or stack trace
```

### Context
What was being attempted when the error occurred

### Root Cause
Analysis of why it happened

### Resolution
How it was fixed or worked around

### Prevention
How to prevent this in the future

### Metadata
- Recurrence-Count: 1
- Related-Issue: #123 (if tracked elsewhere)
- Tags: tag1, tag2
```

## Active Errors

<!-- New errors added here -->

## Fixed Errors

<!-- Moved here after resolution -->

## Recurring Patterns

<!-- Track patterns that appear multiple times -->
