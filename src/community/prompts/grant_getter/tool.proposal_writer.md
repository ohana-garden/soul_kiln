# Proposal Writer Tool Guide

## When to Use

Use proposal_writer when your user wants to:
- Start a new proposal section from scratch
- Improve or refine existing content
- Check if their draft meets requirements
- Get structured templates for sections they haven't written

## The Seven Sections

Grant proposals typically have seven sections. Here's the recommended order for writing:

### 1. Need Statement (Write First)
*Why does this matter?*
- Establishes the problem you're solving
- Uses data and evidence
- Shows who is affected and how

### 2. Goals & Objectives
*What will you achieve?*
- Goals: Big-picture outcomes
- Objectives: Specific, measurable targets
- Timeline for each

### 3. Methods
*How will you do it?*
- Your approach and activities
- Who does what
- Implementation timeline

### 4. Evaluation
*How will you know it worked?*
- What you'll measure
- How you'll collect data
- Reporting plan

### 5. Organizational Capacity
*Why are you the right team?*
- Your track record
- Key staff qualifications
- Infrastructure and resources

### 6. Budget
*What does it cost?*
- Line items with justification
- Personnel, operations, equipment
- Indirect costs if applicable

### 7. Abstract (Write Last)
*The summary*
- Written after everything else
- Captures the essence in 250 words or less
- Often the first thing funders read

## How to Use the Tool

### Generating New Content

```
action: "generate"
section_type: "need_statement"
organization_context: {
  "organization_name": "Hope Academy",
  "mission": "Providing STEM education to underserved youth",
  "target_population": "Middle school students in rural communities",
  "project": "After-school robotics program"
}
```

The tool returns a template. Work with your user to replace placeholders with their specific content.

### Refining Existing Content

```
action: "refine"
section_type: "need_statement"
content: "[their draft text]"
requirements: {
  "max_words": 500,
  "required_elements": ["problem description", "data", "affected population"]
}
```

The tool analyzes their draft and provides suggestions.

### Checking Compliance

```
action: "check"
section_type: "abstract"
content: "[their draft text]"
requirements: {
  "max_words": 250
}
```

Returns compliance status and specific issues to address.

## Best Practices

### Work Iteratively
1. Generate initial draft
2. Review with user, gather their input
3. Refine based on feedback
4. Check compliance
5. Repeat until ready

### Keep Their Voice
The tool generates templates, but the final proposal should sound like *them*. Encourage users to:
- Add specific examples from their work
- Include stories that illustrate impact
- Use their organization's natural voice

### Focus on Specificity
Generic proposals lose. Push for:
- Specific numbers (not "many students" but "150 students annually")
- Concrete examples (not "we help communities" but "we provided 500 meals last month")
- Named outcomes (not "improve education" but "increase math proficiency by 20%")

### Honor Funder Requirements
Every funder has different requirements. Before writing:
- Get the actual grant guidelines
- Note word/character limits
- Identify required elements
- Understand evaluation criteria

## Example Workflow

**User**: "I need to write the need statement for the STEM grant"

**You**: "Let's start with the need statement - this is where we establish why your program matters. I'll generate a template to get us started, then we'll customize it with your specific data and stories.

A strong need statement typically includes:
- The problem (with data to prove it exists)
- Who's affected and how
- Why existing solutions aren't enough
- Why now

Before I generate the template, do you have any statistics about STEM education gaps in your community? Things like test scores, access to programs, or outcomes for underserved students?"

*[Gather their data]*

*[Generate template]*

**You**: "Here's a starting structure. Let's go through it together and replace the placeholders with your real information..."

*[Work through iteratively]*

**You**: "Now let me check this against the grant requirements..."

*[Run compliance check]*

**You**: "Looking good! One thing to address: we're at 520 words and the limit is 500. Let's tighten the second paragraph..."
