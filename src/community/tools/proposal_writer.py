"""
Proposal Writer Tool.

Generates and refines grant proposal sections.
Adapted from Grant-Getter for soul_kiln community framework.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .registry import Tool, ToolResult, ToolCategory

logger = logging.getLogger(__name__)


class SectionType(str, Enum):
    """Types of proposal sections."""

    ABSTRACT = "abstract"
    NEED_STATEMENT = "need_statement"
    GOALS_OBJECTIVES = "goals_objectives"
    METHODS = "methods"
    BUDGET = "budget"
    EVALUATION = "evaluation"
    CAPACITY = "organizational_capacity"


@dataclass
class ProposalSection:
    """A section of a grant proposal."""

    id: str = field(default_factory=lambda: f"section_{uuid.uuid4().hex[:8]}")
    section_type: SectionType = SectionType.ABSTRACT
    title: str = ""
    content: str = ""
    word_count: int = 0
    target_word_count: int = 0
    compliance_status: str = "pending"
    suggestions: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Calculate word count after initialization."""
        self.word_count = len(self.content.split()) if self.content else 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "section_type": self.section_type.value,
            "title": self.title,
            "content": self.content,
            "word_count": self.word_count,
            "target_word_count": self.target_word_count,
            "compliance_status": self.compliance_status,
            "suggestions": self.suggestions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


# Default section requirements
DEFAULT_REQUIREMENTS = {
    SectionType.ABSTRACT: {
        "max_words": 250,
        "required_elements": ["project summary", "funding request", "expected outcomes"],
    },
    SectionType.NEED_STATEMENT: {
        "max_words": 500,
        "required_elements": ["problem description", "affected population", "data/evidence"],
    },
    SectionType.GOALS_OBJECTIVES: {
        "max_words": 400,
        "required_elements": ["goals", "measurable objectives", "timeline"],
    },
    SectionType.METHODS: {
        "max_words": 600,
        "required_elements": ["approach", "activities", "responsible parties"],
    },
    SectionType.BUDGET: {
        "max_words": 300,
        "required_elements": ["budget breakdown", "justification"],
    },
    SectionType.EVALUATION: {
        "max_words": 400,
        "required_elements": ["evaluation methods", "success metrics", "reporting"],
    },
    SectionType.CAPACITY: {
        "max_words": 400,
        "required_elements": ["organizational history", "qualifications", "past successes"],
    },
}

# Template content for each section type
SECTION_TEMPLATES = {
    SectionType.ABSTRACT: """
[Organization Name] requests [funding amount] to [brief project description].

The project will address [primary need] by [key approach]. Our target population
includes [beneficiaries description].

Expected outcomes include:
- [Outcome 1]
- [Outcome 2]
- [Outcome 3]

The project will be implemented over [timeline] and will result in [impact statement].
""",
    SectionType.NEED_STATEMENT: """
[Community/Population] faces significant challenges related to [problem area].

Current data indicates:
- [Statistic 1 demonstrating need]
- [Statistic 2 demonstrating need]
- [Statistic 3 demonstrating need]

The affected population includes [description of who is impacted], comprising
approximately [number] individuals in [geographic area].

Without intervention, [consequences of inaction]. Our proposed project directly
addresses this need by [connection to proposed solution].
""",
    SectionType.GOALS_OBJECTIVES: """
Project Goal: [Overarching goal statement]

Objective 1: [Specific, measurable objective]
- Timeline: [Start date] to [End date]
- Metrics: [How success will be measured]

Objective 2: [Specific, measurable objective]
- Timeline: [Start date] to [End date]
- Metrics: [How success will be measured]

Objective 3: [Specific, measurable objective]
- Timeline: [Start date] to [End date]
- Metrics: [How success will be measured]
""",
    SectionType.METHODS: """
Implementation Approach:

Phase 1: [Phase name] ([Timeline])
- Activity: [Description]
- Responsible: [Staff/role]
- Deliverables: [Expected outputs]

Phase 2: [Phase name] ([Timeline])
- Activity: [Description]
- Responsible: [Staff/role]
- Deliverables: [Expected outputs]

Phase 3: [Phase name] ([Timeline])
- Activity: [Description]
- Responsible: [Staff/role]
- Deliverables: [Expected outputs]

Key partnerships include [partner organizations] who will [their role].
""",
    SectionType.BUDGET: """
Budget Summary:

Personnel: $[amount]
- [Position 1]: $[amount] ([justification])
- [Position 2]: $[amount] ([justification])

Operations: $[amount]
- [Item 1]: $[amount] ([justification])
- [Item 2]: $[amount] ([justification])

Equipment/Supplies: $[amount]
- [Item 1]: $[amount] ([justification])

Indirect Costs: $[amount] ([rate]%)

Total Request: $[total amount]
""",
    SectionType.EVALUATION: """
Evaluation Framework:

Data Collection Methods:
- [Method 1]: [Description and frequency]
- [Method 2]: [Description and frequency]

Success Metrics:
- [Metric 1]: Target of [value] by [date]
- [Metric 2]: Target of [value] by [date]
- [Metric 3]: Target of [value] by [date]

Reporting Schedule:
- Quarterly progress reports
- Mid-term evaluation at [date]
- Final report within [timeframe] of project completion

External evaluator: [If applicable]
""",
    SectionType.CAPACITY: """
Organizational Background:
[Organization name] was founded in [year] with a mission to [mission statement].
Over [number] years, we have served [number] individuals through [types of programs].

Relevant Experience:
- [Past project 1]: [Brief description and outcomes]
- [Past project 2]: [Brief description and outcomes]

Key Personnel:
- [Name], [Title]: [Qualifications and relevant experience]
- [Name], [Title]: [Qualifications and relevant experience]

Infrastructure:
[Description of organizational capacity, facilities, systems, etc.]
""",
}


class ProposalWriter(Tool):
    """
    Tool for generating and refining grant proposal sections.

    Features:
    - Generate proposal sections from templates
    - Refine existing content
    - Check compliance with requirements
    - Provide improvement suggestions
    """

    def __init__(self):
        """Initialize the proposal writer tool."""
        super().__init__()
        self.id = "tool_proposal_writer"
        self.name = "Proposal Writer"
        self.description = "Generate and refine grant proposal sections"
        self.category = ToolCategory.CREATION
        self.version = "1.0.0"

    def execute(
        self,
        action: str = "generate",
        section_type: str = "abstract",
        content: str | None = None,
        organization_context: dict | None = None,
        requirements: dict | None = None,
        **kwargs,
    ) -> ToolResult:
        """
        Execute proposal writing action.

        Args:
            action: "generate", "refine", or "check"
            section_type: Type of section to work with
            content: Existing content (for refine/check)
            organization_context: Organization details for personalization
            requirements: Custom requirements (overrides defaults)

        Returns:
            ToolResult with section content and metadata
        """
        try:
            # Parse section type
            try:
                sec_type = SectionType(section_type.lower())
            except ValueError:
                return ToolResult(
                    success=False,
                    error=f"Invalid section type: {section_type}. Valid types: {[s.value for s in SectionType]}",
                )

            # Get requirements
            reqs = requirements or DEFAULT_REQUIREMENTS.get(sec_type, {})

            if action == "generate":
                section = self._generate_section(sec_type, organization_context, reqs)
            elif action == "refine":
                if not content:
                    return ToolResult(
                        success=False,
                        error="Content required for refine action",
                    )
                section = self._refine_section(sec_type, content, organization_context, reqs)
            elif action == "check":
                if not content:
                    return ToolResult(
                        success=False,
                        error="Content required for check action",
                    )
                section = self._check_section(sec_type, content, reqs)
            else:
                return ToolResult(
                    success=False,
                    error=f"Invalid action: {action}. Valid actions: generate, refine, check",
                )

            return ToolResult(
                success=True,
                data=section.to_dict(),
                metadata={
                    "action": action,
                    "section_type": sec_type.value,
                    "requirements": reqs,
                },
            )

        except Exception as e:
            logger.error(f"Proposal writer error: {e}")
            return ToolResult(
                success=False,
                error=str(e),
            )

    def _generate_section(
        self,
        section_type: SectionType,
        organization_context: dict | None,
        requirements: dict,
    ) -> ProposalSection:
        """Generate a proposal section from template."""
        template = SECTION_TEMPLATES.get(section_type, "")

        # Personalize if context provided
        content = template.strip()
        if organization_context:
            for key, value in organization_context.items():
                placeholder = f"[{key}]"
                content = content.replace(placeholder, str(value))

        section = ProposalSection(
            section_type=section_type,
            title=section_type.value.replace("_", " ").title(),
            content=content,
            target_word_count=requirements.get("max_words", 500),
        )

        # Generate suggestions
        section.suggestions = self._generate_suggestions(section, requirements)
        section.compliance_status = self._calculate_compliance_status(section, requirements)

        return section

    def _refine_section(
        self,
        section_type: SectionType,
        content: str,
        organization_context: dict | None,
        requirements: dict,
    ) -> ProposalSection:
        """Refine existing content."""
        section = ProposalSection(
            section_type=section_type,
            title=section_type.value.replace("_", " ").title(),
            content=content,
            target_word_count=requirements.get("max_words", 500),
        )

        # Analyze and provide suggestions
        section.suggestions = self._generate_suggestions(section, requirements)
        section.compliance_status = self._calculate_compliance_status(section, requirements)

        return section

    def _check_section(
        self,
        section_type: SectionType,
        content: str,
        requirements: dict,
    ) -> ProposalSection:
        """Check content against requirements."""
        section = ProposalSection(
            section_type=section_type,
            title=section_type.value.replace("_", " ").title(),
            content=content,
            target_word_count=requirements.get("max_words", 500),
        )

        section.suggestions = self._generate_suggestions(section, requirements)
        section.compliance_status = self._calculate_compliance_status(section, requirements)

        return section

    def _generate_suggestions(
        self,
        section: ProposalSection,
        requirements: dict,
    ) -> list[str]:
        """Generate improvement suggestions."""
        suggestions = []
        content_lower = section.content.lower()

        # Word count check
        max_words = requirements.get("max_words", 500)
        if section.word_count > max_words:
            suggestions.append(
                f"Reduce word count from {section.word_count} to {max_words} or fewer"
            )
        elif section.word_count < max_words * 0.5:
            suggestions.append(
                f"Consider expanding content (currently {section.word_count} words, "
                f"target is around {max_words})"
            )

        # Required elements check
        required = requirements.get("required_elements", [])
        for element in required:
            # Simple keyword check
            element_words = element.lower().split()
            if not any(word in content_lower for word in element_words):
                suggestions.append(f"Consider adding: {element}")

        # Check for placeholder brackets
        if "[" in section.content and "]" in section.content:
            suggestions.append("Replace placeholder text in [brackets] with actual content")

        # Check for specificity
        vague_words = ["some", "many", "various", "several", "etc"]
        for word in vague_words:
            if f" {word} " in content_lower:
                suggestions.append(f"Replace vague term '{word}' with specific details")

        return suggestions

    def _calculate_compliance_status(
        self,
        section: ProposalSection,
        requirements: dict,
    ) -> str:
        """Calculate compliance status."""
        issues = 0

        # Word count
        max_words = requirements.get("max_words", 500)
        if section.word_count > max_words:
            issues += 1

        # Placeholders
        if "[" in section.content:
            issues += 1

        # Required elements
        required = requirements.get("required_elements", [])
        content_lower = section.content.lower()
        missing = 0
        for element in required:
            element_words = element.lower().split()
            if not any(word in content_lower for word in element_words):
                missing += 1
        if missing > len(required) / 2:
            issues += 1

        if issues == 0:
            return "compliant"
        elif issues == 1:
            return "minor_issues"
        else:
            return "needs_work"

    def get_schema(self) -> dict:
        """Get the tool's input schema."""
        return {
            "type": "object",
            "required": ["action", "section_type"],
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["generate", "refine", "check"],
                    "description": "Action to perform",
                },
                "section_type": {
                    "type": "string",
                    "enum": [s.value for s in SectionType],
                    "description": "Type of proposal section",
                },
                "content": {
                    "type": "string",
                    "description": "Existing content (for refine/check)",
                },
                "organization_context": {
                    "type": "object",
                    "description": "Organization details for personalization",
                },
                "requirements": {
                    "type": "object",
                    "description": "Custom requirements",
                },
            },
        }
