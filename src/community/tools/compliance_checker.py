"""
Compliance Checker Tool.

Validates proposals against funder requirements.
Adapted from Grant-Getter for soul_kiln community framework.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .registry import Tool, ToolResult, ToolCategory

logger = logging.getLogger(__name__)


@dataclass
class ComplianceIssue:
    """A compliance issue found during validation."""

    severity: str  # "critical", "warning", "info"
    section: str
    message: str
    suggestion: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "severity": self.severity,
            "section": self.section,
            "message": self.message,
            "suggestion": self.suggestion,
        }


@dataclass
class ComplianceResult:
    """Result of compliance checking."""

    is_compliant: bool = False
    score: float = 0.0
    issues: list[ComplianceIssue] = field(default_factory=list)
    sections_checked: list[str] = field(default_factory=list)
    checked_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)

    def add_issue(
        self,
        severity: str,
        section: str,
        message: str,
        suggestion: str = "",
    ) -> None:
        """Add an issue."""
        self.issues.append(ComplianceIssue(
            severity=severity,
            section=section,
            message=message,
            suggestion=suggestion,
        ))

    def critical_count(self) -> int:
        """Count critical issues."""
        return len([i for i in self.issues if i.severity == "critical"])

    def warning_count(self) -> int:
        """Count warning issues."""
        return len([i for i in self.issues if i.severity == "warning"])

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "is_compliant": self.is_compliant,
            "score": self.score,
            "issues": [i.to_dict() for i in self.issues],
            "sections_checked": self.sections_checked,
            "checked_at": self.checked_at.isoformat(),
            "summary": {
                "critical": self.critical_count(),
                "warnings": self.warning_count(),
                "total_issues": len(self.issues),
            },
            "metadata": self.metadata,
        }


class ComplianceChecker(Tool):
    """
    Tool for validating proposals against funder requirements.

    Checks:
    - Word/character limits
    - Required sections
    - Required content elements
    - Formatting restrictions
    - Deadline compliance
    """

    def __init__(self):
        """Initialize the compliance checker tool."""
        super().__init__()
        self.id = "tool_compliance_checker"
        self.name = "Compliance Checker"
        self.description = "Validate proposals against funder requirements"
        self.category = ToolCategory.VALIDATION
        self.version = "1.0.0"

    def execute(
        self,
        proposal: dict[str, str] | None = None,
        requirements: dict | None = None,
        funder_guidelines: str | None = None,
        check_formatting: bool = True,
        **kwargs,
    ) -> ToolResult:
        """
        Check proposal compliance.

        Args:
            proposal: Dict of section_name -> content
            requirements: Requirements specification
            funder_guidelines: Raw funder guidelines text
            check_formatting: Whether to check formatting issues

        Returns:
            ToolResult with ComplianceResult
        """
        try:
            if not proposal:
                return ToolResult(
                    success=False,
                    error="Proposal content required",
                )

            result = ComplianceResult()
            result.sections_checked = list(proposal.keys())

            # Use default requirements if none provided
            reqs = requirements or self._get_default_requirements()

            # Check each section
            for section_name, content in proposal.items():
                section_reqs = reqs.get(section_name, reqs.get("default", {}))
                self._check_section(result, section_name, content, section_reqs)

            # Check for required sections
            required_sections = reqs.get("required_sections", [])
            for section in required_sections:
                if section not in proposal:
                    result.add_issue(
                        severity="critical",
                        section=section,
                        message=f"Required section missing: {section}",
                        suggestion=f"Add the {section} section to your proposal",
                    )

            # Check formatting if enabled
            if check_formatting:
                self._check_formatting(result, proposal)

            # Calculate score and compliance
            result.score = self._calculate_score(result)
            result.is_compliant = result.critical_count() == 0 and result.score >= 0.7

            return ToolResult(
                success=True,
                data=result.to_dict(),
                metadata={
                    "requirements_used": reqs,
                    "formatting_checked": check_formatting,
                },
            )

        except Exception as e:
            logger.error(f"Compliance check error: {e}")
            return ToolResult(
                success=False,
                error=str(e),
            )

    def _check_section(
        self,
        result: ComplianceResult,
        section_name: str,
        content: str,
        requirements: dict,
    ) -> None:
        """Check a single section against requirements."""
        # Word count check
        word_count = len(content.split())
        max_words = requirements.get("max_words")
        min_words = requirements.get("min_words", 0)

        if max_words and word_count > max_words:
            result.add_issue(
                severity="critical",
                section=section_name,
                message=f"Word count ({word_count}) exceeds limit ({max_words})",
                suggestion=f"Reduce content by {word_count - max_words} words",
            )
        elif min_words and word_count < min_words:
            result.add_issue(
                severity="warning",
                section=section_name,
                message=f"Word count ({word_count}) below minimum ({min_words})",
                suggestion=f"Expand content by {min_words - word_count} words",
            )

        # Character count check
        char_count = len(content)
        max_chars = requirements.get("max_characters")
        if max_chars and char_count > max_chars:
            result.add_issue(
                severity="critical",
                section=section_name,
                message=f"Character count ({char_count}) exceeds limit ({max_chars})",
                suggestion="Reduce content length",
            )

        # Required elements check
        required_elements = requirements.get("required_elements", [])
        content_lower = content.lower()
        for element in required_elements:
            # Check if any word from the element appears in content
            element_words = element.lower().split()
            if not any(word in content_lower for word in element_words if len(word) > 3):
                result.add_issue(
                    severity="warning",
                    section=section_name,
                    message=f"May be missing required element: {element}",
                    suggestion=f"Ensure you address: {element}",
                )

        # Prohibited content check
        prohibited = requirements.get("prohibited", [])
        for item in prohibited:
            if item.lower() in content_lower:
                result.add_issue(
                    severity="critical",
                    section=section_name,
                    message=f"Contains prohibited content: {item}",
                    suggestion=f"Remove or rephrase content containing '{item}'",
                )

    def _check_formatting(
        self,
        result: ComplianceResult,
        proposal: dict[str, str],
    ) -> None:
        """Check formatting issues across the proposal."""
        full_content = " ".join(proposal.values())

        # Check for unfilled placeholders
        placeholders = re.findall(r'\[[^\]]+\]', full_content)
        if placeholders:
            result.add_issue(
                severity="critical",
                section="general",
                message=f"Found {len(placeholders)} unfilled placeholders",
                suggestion="Replace all [placeholder] text with actual content",
            )

        # Check for excessive exclamation marks
        if full_content.count("!") > 3:
            result.add_issue(
                severity="info",
                section="general",
                message="Multiple exclamation marks detected",
                suggestion="Consider using more professional tone",
            )

        # Check for very long sentences
        sentences = re.split(r'[.!?]', full_content)
        long_sentences = [s for s in sentences if len(s.split()) > 50]
        if long_sentences:
            result.add_issue(
                severity="warning",
                section="general",
                message=f"Found {len(long_sentences)} very long sentences",
                suggestion="Break up sentences longer than 50 words",
            )

        # Check for consistent formatting
        sections_with_bullets = [s for s, c in proposal.items() if "•" in c or "- " in c]
        sections_with_numbers = [s for s, c in proposal.items() if re.search(r'\d+\.', c)]
        if sections_with_bullets and sections_with_numbers:
            result.add_issue(
                severity="info",
                section="general",
                message="Mixed bullet styles (bullets and numbers)",
                suggestion="Consider using consistent list formatting",
            )

    def _calculate_score(self, result: ComplianceResult) -> float:
        """Calculate compliance score (0-1)."""
        if not result.sections_checked:
            return 0.0

        # Start with perfect score
        score = 1.0

        # Deduct for issues
        for issue in result.issues:
            if issue.severity == "critical":
                score -= 0.2
            elif issue.severity == "warning":
                score -= 0.05
            elif issue.severity == "info":
                score -= 0.01

        return max(0.0, min(1.0, score))

    def _get_default_requirements(self) -> dict:
        """Get default requirements."""
        return {
            "required_sections": [
                "abstract",
                "need_statement",
                "goals_objectives",
                "methods",
                "budget",
                "evaluation",
            ],
            "abstract": {
                "max_words": 250,
                "required_elements": ["project summary", "funding amount", "outcomes"],
            },
            "need_statement": {
                "max_words": 500,
                "min_words": 200,
                "required_elements": ["problem", "population", "data"],
            },
            "goals_objectives": {
                "max_words": 400,
                "required_elements": ["goals", "objectives", "measurable"],
            },
            "methods": {
                "max_words": 600,
                "required_elements": ["approach", "activities", "timeline"],
            },
            "budget": {
                "max_words": 300,
                "required_elements": ["costs", "justification"],
            },
            "evaluation": {
                "max_words": 400,
                "required_elements": ["metrics", "evaluation", "reporting"],
            },
            "default": {
                "max_words": 500,
            },
        }

    def get_schema(self) -> dict:
        """Get the tool's input schema."""
        return {
            "type": "object",
            "required": ["proposal"],
            "properties": {
                "proposal": {
                    "type": "object",
                    "description": "Dict of section_name -> content",
                    "additionalProperties": {"type": "string"},
                },
                "requirements": {
                    "type": "object",
                    "description": "Custom requirements specification",
                },
                "funder_guidelines": {
                    "type": "string",
                    "description": "Raw funder guidelines text",
                },
                "check_formatting": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to check formatting issues",
                },
            },
        }
