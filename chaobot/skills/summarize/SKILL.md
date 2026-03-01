---
name: summarize
description: "Summarize URLs, files, and long text content into concise summaries"
homepage: https://github.com/HKUDS/nanobot
metadata: {"chaobot":{"emoji":"📝","requires":{}}}
---

# Summarize Skill

Summarize long content from URLs, files, or text into concise, readable summaries.

## When to Use

Use this skill when:
- User shares a URL and wants a summary
- User pastes long text that needs condensation
- User uploads a document to summarize
- You need to extract key points from research

## Summarization Guidelines

### URL Summarization

For web pages and articles:
```
1. Fetch the content using web_fetch tool
2. Extract the main text (ignore navigation, ads, etc.)
3. Identify key points and main arguments
4. Create a concise summary (20% of original length)
5. Include important quotes or data points
```

### File Summarization

For documents and code:
```
1. Read the file content
2. Identify the structure and purpose
3. Extract key sections and findings
4. Summarize technical details appropriately
5. Note any action items or conclusions
```

### Text Summarization

For pasted content:
```
1. Identify the main topic and purpose
2. Extract key arguments or points
3. Remove redundant information
4. Preserve important details and numbers
5. Structure with bullet points for readability
```

## Summary Format

Use this structure for summaries:

```markdown
## Summary

**Main Topic:** [One sentence description]

**Key Points:**
- Point 1
- Point 2
- Point 3

**Important Details:**
- Specific data, quotes, or findings

**Conclusion/Action Items:**
- What this means or what to do next
```

## Examples

**Article Summary:**
```
URL: https://example.com/ai-article

## Summary

**Main Topic:** New AI model achieves breakthrough in natural language understanding

**Key Points:**
- Model trained on 10x more data than previous version
- Achieves 95% accuracy on benchmark tests
- Open source and available for research

**Important Details:**
- Training cost: $10 million
- Release date: March 2024
- GitHub: github.com/example/model

**Conclusion:**
This represents significant progress in AI capabilities and will likely accelerate research in the field.
```

**Code Summary:**
```
File: main.py (150 lines)

## Summary

**Main Topic:** FastAPI application with user authentication

**Key Components:**
- User registration/login endpoints
- JWT token authentication
- Database models with SQLAlchemy
- Password hashing with bcrypt

**Important Details:**
- Uses async/await throughout
- Includes rate limiting middleware
- Has comprehensive error handling

**Conclusion:**
Well-structured authentication system ready for production use.
```

## Best Practices

1. **Be concise** - Aim for 20-30% of original length
2. **Preserve accuracy** - Don't change the meaning
3. **Include context** - Explain why the content matters
4. **Highlight key data** - Numbers, dates, names are important
5. **Use structure** - Bullet points improve readability
6. **Note limitations** - Mention if content was truncated

## Length Guidelines

| Original Length | Target Summary |
|----------------|----------------|
| < 500 words | 50-100 words |
| 500-2000 words | 100-300 words |
| 2000-5000 words | 300-500 words |
| > 5000 words | 500-800 words |

## Special Cases

**Research Papers:**
- Include: hypothesis, methodology, key findings, conclusion
- Note: sample size, significance levels

**News Articles:**
- Include: who, what, when, where, why
- Note: sources and credibility

**Technical Docs:**
- Include: purpose, usage, examples, limitations
- Note: version and compatibility

**Code:**
- Include: purpose, key functions, dependencies
- Note: architecture patterns used
