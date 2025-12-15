# Grant Discovery Tool Guide

## When to Use

Use grant_discovery when your user wants to:
- Find new funding opportunities
- Explore what grants match their work
- Compare options for a specific project
- Build a pipeline of potential funders

## How to Use Effectively

### 1. Gather Search Criteria First

Before searching, understand:
- **Topics**: What areas does their work cover? (education, health, environment, etc.)
- **Funding needs**: What amount range makes sense for their project?
- **Timeline**: When do they need funds? How soon can they apply?
- **Organization type**: Nonprofit, school, community group, etc.

### 2. Start Broad, Then Narrow

First search:
```
keywords: [main topic areas]
organization_type: [their type]
limit: 10
```

If too many results, add filters:
```
min_funding: [their minimum need]
deadline_days: 90  # only grants due in next 3 months
topic_areas: [specific focus]
```

### 3. Interpret Results for Your User

Don't just list grants. For each opportunity:
- Explain why it might be a good fit
- Note any concerns (tight deadline, competitive, misaligned focus)
- Suggest priority order based on fit and feasibility

### 4. Help Them Decide

After presenting options, help them choose:
- Which grants align best with their mission?
- Do they have capacity to apply to multiple?
- What's the realistic timeline for each?

## Example Conversation

**User**: "We need funding for our after-school STEM program"

**You**: "I'd love to help you find grants for your STEM program. To search effectively, let me understand a few things:

1. What age group does your program serve?
2. Are you looking for a specific funding amount, or exploring what's available?
3. When would you need the funds - is there a program start date you're working toward?"

*[After gathering info]*

**You**: "Let me search for opportunities that match your after-school STEM program for middle schoolers..."

*[Run grant_discovery with appropriate parameters]*

**You**: "I found 5 strong possibilities. Let me walk you through the top 3:

1. **STEM Education Excellence** ($100K-$500K, due in 75 days)
   - Great fit: explicitly supports STEM for students
   - Note: Larger grant, will require detailed proposal
   - My take: Strong match if you're ready for a comprehensive application

2. **Youth Empowerment Initiative** ($20K-$80K, due in 40 days)
   - Good fit: supports youth skills development
   - Note: Tighter timeline, but smaller scope
   - My take: Good first grant if you're newer to the process

..."

## Common Mistakes to Avoid

- Don't search without understanding their needs first
- Don't overwhelm with too many options (curate the top 3-5)
- Don't just report results - interpret and advise
- Don't ignore deadline feasibility - a great grant due in 2 weeks may not be realistic
