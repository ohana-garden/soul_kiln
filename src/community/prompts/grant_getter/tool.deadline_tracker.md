# Deadline Tracker Tool Guide

## When to Use

Use deadline_tracker when:
- Managing multiple grant opportunities
- Planning application timelines
- Checking what's due soon
- Creating work schedules for proposals

## How to Use Effectively

### 1. Track All Active Opportunities

Add deadlines as they're identified:
```
action: "add"
funder: "STEM Education Fund"
deadline: "2024-03-15"
priority: "high"
notes: "Requires 3 letters of support"
```

### 2. Regular Check-ins

Query upcoming deadlines:
```
action: "list"
days_ahead: 30
priority_filter: "high"
```

### 3. Interpret Timeline for Your User

When presenting deadlines:
- Calculate working days until due
- Consider prep time needed (letters, reviews, approvals)
- Flag conflicts if multiple are due close together

### 4. Help Prioritize

Based on deadlines and requirements:
- What's most urgent?
- What has the best ROI of effort?
- What might need to be deferred?

## Example Conversation

**User**: "What grants do I need to focus on this month?"

**You**: "Let me check your active deadlines..."

*[Run deadline_tracker to list upcoming]*

**You**: "Here's your grant landscape for the next 30 days:

**Urgent (Due This Week)**:
- *Youth Innovation Fund* - Due Friday (4 days)
  - Status: Draft complete, needs final review
  - Action needed: Schedule board review, submit

**Coming Up (Next 2 Weeks)**:
- *Community Health Initiative* - Due in 12 days
  - Status: Need statement done, methods in progress
  - Action needed: Complete budget, get finance review

**On the Horizon**:
- *Environmental Justice Grant* - Due in 28 days
  - Status: Early research phase
  - Action needed: Start drafting after Youth Innovation submits

I recommend focusing entirely on Youth Innovation this week. Want me to help create a day-by-day plan for these 4 days?"

## Deadline Management Tips

### Setting Realistic Timelines
- Add 2-3 days buffer before actual deadline
- Account for internal review cycles
- Plan for letter of support collection (often 2+ weeks)

### Handling Conflicts
- Identify overlapping deadlines early
- Consider which grants are better fits
- Sometimes it's better to do one well than two poorly

## Common Mistakes to Avoid

- Don't track just the final deadline - add internal milestones
- Don't ignore low-priority items - they become urgent
- Don't overcommit - be realistic about capacity
- Don't forget recurring grants - add next year's dates when one closes
