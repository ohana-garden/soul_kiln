# Compliance Checker Tool Guide

## When to Use

Use compliance_checker when:
- A proposal draft is ready for review
- Checking if requirements are met before submission
- Validating sections against funder guidelines
- Identifying missing or incomplete elements

## How to Use Effectively

### 1. Gather Requirements First

Before checking, ensure you have:
- **Funder guidelines**: The official requirements document
- **Proposal content**: The sections to validate
- **Specific requirements**: Word limits, required sections, formatting rules

### 2. Run Comprehensive Checks

```
proposal: {
  "abstract": "...",
  "need_statement": "...",
  "methods": "..."
}
requirements: {
  "word_limits": {"abstract": 250, "need_statement": 500},
  "required_sections": ["abstract", "need_statement", "goals", "methods", "budget"]
}
check_formatting: true
```

### 3. Interpret Results for Your User

The checker returns:
- **issues**: Problems that must be fixed
- **warnings**: Concerns to consider
- **passed_checks**: What's looking good
- **compliance_score**: Overall percentage

For each issue:
- Explain why it matters
- Suggest how to fix it
- Prioritize by severity

### 4. Guide Revisions

After presenting issues:
- Start with blocking issues (word limits, missing sections)
- Then address warnings
- Celebrate what's passing

## Example Conversation

**User**: "Can you check if my proposal is ready to submit?"

**You**: "I'll run a compliance check against the funder's requirements. Let me review your current draft..."

*[Run compliance_checker with proposal and requirements]*

**You**: "Here's what I found:

**Must Fix** (2 issues):
1. Your abstract is 312 words - the limit is 250. You'll need to cut about 60 words.
2. Missing 'Evaluation Plan' section - this is required.

**Recommendations** (1 warning):
- Your budget narrative is brief. While not required, funders often appreciate more detail on major expenses.

**Looking Good**:
- All required sections present (except evaluation)
- Word counts within limits for other sections
- Formatting follows guidelines

Your compliance score is 78%. Let's tackle the abstract first - would you like help trimming it?"

## Common Mistakes to Avoid

- Don't check without having the actual requirements
- Don't ignore warnings - they can affect competitiveness
- Don't just list issues - help prioritize and solve them
- Don't skip formatting checks - they matter to reviewers
