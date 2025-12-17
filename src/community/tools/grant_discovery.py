"""
Grant Discovery Tool.

Searches for grant opportunities across funding sources.
Adapted from Grant-Getter for soul_kiln community framework.
"""

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .registry import Tool, ToolResult, ToolCategory

logger = logging.getLogger(__name__)


@dataclass
class GrantOpportunity:
    """A grant funding opportunity."""

    id: str = field(default_factory=lambda: f"grant_{uuid.uuid4().hex[:8]}")
    title: str = ""
    funder: str = ""
    description: str = ""
    funding_min: float = 0.0
    funding_max: float = 0.0
    deadline: datetime | None = None
    eligibility: list[str] = field(default_factory=list)
    topic_areas: list[str] = field(default_factory=list)
    url: str = ""
    relevance_score: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "funder": self.funder,
            "description": self.description,
            "funding_range": {
                "min": self.funding_min,
                "max": self.funding_max,
            },
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "eligibility": self.eligibility,
            "topic_areas": self.topic_areas,
            "url": self.url,
            "relevance_score": self.relevance_score,
            "metadata": self.metadata,
        }


class GrantDiscovery(Tool):
    """
    Tool for discovering grant opportunities.

    Searches funding databases and ranks results by relevance.
    Currently uses mock data for testing - production would
    integrate with Grants.gov and other funding APIs.
    """

    def __init__(self):
        """Initialize the grant discovery tool."""
        super().__init__()
        self.id = "tool_grant_discovery"
        self.name = "Grant Discovery"
        self.description = "Search for grant funding opportunities"
        self.category = ToolCategory.DISCOVERY
        self.version = "1.0.0"

    def execute(
        self,
        keywords: list[str] | None = None,
        organization_type: str = "nonprofit",
        topic_areas: list[str] | None = None,
        min_funding: float | None = None,
        max_funding: float | None = None,
        deadline_days: int | None = None,
        limit: int = 10,
        **kwargs,
    ) -> ToolResult:
        """
        Search for grant opportunities.

        Args:
            keywords: Search keywords
            organization_type: Type of organization (nonprofit, education, etc.)
            topic_areas: Topics to filter by
            min_funding: Minimum funding amount
            max_funding: Maximum funding amount
            deadline_days: Only grants due within this many days
            limit: Maximum results to return

        Returns:
            ToolResult with list of GrantOpportunity objects
        """
        try:
            # Generate mock grants (in production, query APIs)
            all_grants = self._generate_mock_grants(keywords or [], organization_type)

            # Apply filters
            filtered = self._filter_opportunities(
                grants=all_grants,
                min_funding=min_funding,
                max_funding=max_funding,
                deadline_days=deadline_days,
                topic_areas=topic_areas,
            )

            # Rank by relevance
            ranked = self._rank_opportunities(
                grants=filtered,
                keywords=keywords or [],
                topic_areas=topic_areas or [],
                organization_type=organization_type,
            )

            # Limit results
            results = ranked[:limit]

            return ToolResult(
                success=True,
                data={
                    "grants": [g.to_dict() for g in results],
                    "total_found": len(all_grants),
                    "after_filters": len(filtered),
                    "returned": len(results),
                },
                metadata={
                    "search_params": {
                        "keywords": keywords,
                        "organization_type": organization_type,
                        "topic_areas": topic_areas,
                        "min_funding": min_funding,
                        "max_funding": max_funding,
                        "deadline_days": deadline_days,
                    },
                },
            )

        except Exception as e:
            logger.error(f"Grant discovery error: {e}")
            return ToolResult(
                success=False,
                error=str(e),
            )

    def _generate_mock_grants(
        self,
        keywords: list[str],
        organization_type: str,
    ) -> list[GrantOpportunity]:
        """Generate mock grant data for testing."""
        now = datetime.utcnow()

        mock_grants = [
            GrantOpportunity(
                id="grant_edu_001",
                title="Education Innovation Grant",
                funder="Department of Education",
                description="Supporting innovative educational programs for underserved communities",
                funding_min=50000,
                funding_max=250000,
                deadline=now + timedelta(days=45),
                eligibility=["nonprofit", "education", "school"],
                topic_areas=["education", "technology", "youth"],
                url="https://grants.gov/education-innovation",
            ),
            GrantOpportunity(
                id="grant_health_001",
                title="Community Health Initiative",
                funder="National Health Foundation",
                description="Grants for community-based health programs",
                funding_min=25000,
                funding_max=100000,
                deadline=now + timedelta(days=30),
                eligibility=["nonprofit", "health", "community"],
                topic_areas=["health", "community", "wellness"],
                url="https://grants.gov/community-health",
            ),
            GrantOpportunity(
                id="grant_env_001",
                title="Environmental Sustainability Program",
                funder="Green Future Foundation",
                description="Supporting environmental conservation and sustainability projects",
                funding_min=10000,
                funding_max=75000,
                deadline=now + timedelta(days=60),
                eligibility=["nonprofit", "education", "community"],
                topic_areas=["environment", "sustainability", "conservation"],
                url="https://grants.gov/env-sustainability",
            ),
            GrantOpportunity(
                id="grant_arts_001",
                title="Arts and Culture Development Grant",
                funder="National Endowment for the Arts",
                description="Supporting arts programs in underserved communities",
                funding_min=15000,
                funding_max=50000,
                deadline=now + timedelta(days=90),
                eligibility=["nonprofit", "arts", "education"],
                topic_areas=["arts", "culture", "community"],
                url="https://grants.gov/arts-culture",
            ),
            GrantOpportunity(
                id="grant_stem_001",
                title="STEM Education Excellence",
                funder="Science Foundation",
                description="Advancing STEM education for students",
                funding_min=100000,
                funding_max=500000,
                deadline=now + timedelta(days=75),
                eligibility=["nonprofit", "education", "school"],
                topic_areas=["education", "stem", "technology", "science"],
                url="https://grants.gov/stem-excellence",
            ),
            GrantOpportunity(
                id="grant_youth_001",
                title="Youth Empowerment Initiative",
                funder="Youth Development Foundation",
                description="Programs empowering youth through mentorship and skills training",
                funding_min=20000,
                funding_max=80000,
                deadline=now + timedelta(days=40),
                eligibility=["nonprofit", "community", "education"],
                topic_areas=["youth", "mentorship", "skills", "employment"],
                url="https://grants.gov/youth-empowerment",
            ),
            GrantOpportunity(
                id="grant_food_001",
                title="Food Security and Nutrition Grant",
                funder="Agricultural Development Fund",
                description="Supporting food security programs in underserved areas",
                funding_min=30000,
                funding_max=150000,
                deadline=now + timedelta(days=55),
                eligibility=["nonprofit", "community", "agriculture"],
                topic_areas=["food", "nutrition", "agriculture", "community"],
                url="https://grants.gov/food-security",
            ),
        ]

        return mock_grants

    def _filter_opportunities(
        self,
        grants: list[GrantOpportunity],
        min_funding: float | None,
        max_funding: float | None,
        deadline_days: int | None,
        topic_areas: list[str] | None,
    ) -> list[GrantOpportunity]:
        """Filter grants by criteria."""
        filtered = []
        now = datetime.utcnow()

        for grant in grants:
            # Filter by funding amount
            if min_funding and grant.funding_max < min_funding:
                continue
            if max_funding and grant.funding_min > max_funding:
                continue

            # Filter by deadline
            if deadline_days and grant.deadline:
                deadline_limit = now + timedelta(days=deadline_days)
                if grant.deadline > deadline_limit:
                    continue

            # Filter by topic areas
            if topic_areas:
                if not any(t.lower() in [ta.lower() for ta in grant.topic_areas] for t in topic_areas):
                    continue

            filtered.append(grant)

        return filtered

    def _rank_opportunities(
        self,
        grants: list[GrantOpportunity],
        keywords: list[str],
        topic_areas: list[str],
        organization_type: str,
    ) -> list[GrantOpportunity]:
        """Rank grants by relevance."""
        for grant in grants:
            score = 0.0

            # Keyword matching in title and description
            text = f"{grant.title} {grant.description}".lower()
            for keyword in keywords:
                if keyword.lower() in text:
                    score += 0.2

            # Topic area overlap
            grant_topics = set(t.lower() for t in grant.topic_areas)
            search_topics = set(t.lower() for t in topic_areas)
            if grant_topics and search_topics:
                overlap = len(grant_topics & search_topics) / len(search_topics)
                score += overlap * 0.3

            # Eligibility match
            if organization_type.lower() in [e.lower() for e in grant.eligibility]:
                score += 0.3

            # Deadline proximity bonus (sooner = higher priority)
            if grant.deadline:
                days_until = (grant.deadline - datetime.utcnow()).days
                if days_until <= 30:
                    score += 0.2
                elif days_until <= 60:
                    score += 0.1

            grant.relevance_score = min(1.0, score)

        # Sort by relevance descending
        grants.sort(key=lambda g: g.relevance_score, reverse=True)
        return grants

    def get_schema(self) -> dict:
        """Get the tool's input schema."""
        return {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Search keywords",
                },
                "organization_type": {
                    "type": "string",
                    "default": "nonprofit",
                    "description": "Type of organization",
                },
                "topic_areas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Topics to filter by",
                },
                "min_funding": {
                    "type": "number",
                    "description": "Minimum funding amount",
                },
                "max_funding": {
                    "type": "number",
                    "description": "Maximum funding amount",
                },
                "deadline_days": {
                    "type": "integer",
                    "description": "Only grants due within this many days",
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum results to return",
                },
            },
        }
