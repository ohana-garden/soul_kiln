"""
Grant-Getter Community Definition.

A community focused on helping students and nonprofits secure grants.
Embodies "I am, because we are" through:
- Agents cooperating to help students
- Sharing knowledge without sharing PII
- Collective learning from successes and failures

Virtue Emphasis:
- Service (V19): High - core purpose is helping others
- Truthfulness (V02): High - honest, accurate proposals
- Justice (V03): High - equitable access to funding
- Wisdom (V16): High - strategic grant matching
- Courtesy (V06): Medium - professional funder relations
- Fidelity (V08): Medium - follow-through on commitments
"""

from ..model import Community, CommunityPurpose, VirtueEmphasis
from ..registry import CommunityRegistry, get_registry
from ..tools import (
    GrantDiscovery,
    ProposalWriter,
    ComplianceChecker,
    DeadlineTracker,
    get_tool_registry,
)

# Tool IDs for Grant-Getter community
GRANT_GETTER_TOOLS = [
    "tool_grant_discovery",
    "tool_proposal_writer",
    "tool_compliance_checker",
    "tool_deadline_tracker",
]


def create_grant_getter_community(
    registry: CommunityRegistry | None = None,
    created_by: str = "system",
    register_tools: bool = True,
) -> Community:
    """
    Create the Grant-Getter community.

    This community focuses on helping students and nonprofits
    secure grant funding through cooperative agent assistance.

    Args:
        registry: Community registry (uses singleton if not provided)
        created_by: Creator ID
        register_tools: Whether to register tools in tool registry

    Returns:
        Created Grant-Getter community
    """
    registry = registry or get_registry()

    # Check if already exists
    existing = registry.get_by_name("Grant-Getter")
    if existing:
        return existing

    # Define virtue emphasis for grant work
    virtue_emphasis = VirtueEmphasis(
        cluster_modifiers={
            # Relational virtues emphasized - grants are about relationships
            "relational": 0.05,
            # Transcendent virtues also emphasized - service is key
            "transcendent": 0.05,
        },
        virtue_modifiers={
            # Core emphasis virtues
            "V19": 0.15,  # Service - highest emphasis, core purpose
            "V02": 0.10,  # Truthfulness - honest proposals
            "V03": 0.10,  # Justice - equitable access
            "V16": 0.10,  # Wisdom - strategic decisions

            # Supporting virtues
            "V06": 0.05,  # Courtesy - professional relations
            "V08": 0.05,  # Fidelity - follow-through
            "V07": 0.05,  # Forbearance - patience with process
            "V13": 0.05,  # Goodwill - benevolent intent
        },
        rationale=(
            "Grant-Getter emphasizes Service as its core virtue - the entire purpose "
            "is helping students and nonprofits access resources. Truthfulness ensures "
            "proposals are honest and accurate. Justice promotes equitable access to "
            "funding. Wisdom guides strategic grant matching. Supporting virtues ensure "
            "professional conduct and persistent follow-through."
        ),
    )

    # Create the community
    community = registry.create(
        name="Grant-Getter",
        description=(
            "A community of agents helping students and nonprofits secure grant funding. "
            "Agents cooperate to discover opportunities, write compelling proposals, "
            "ensure compliance, and track deadlines. Knowledge is shared freely - "
            "successful patterns benefit all. 'I am, because we are.'"
        ),
        purpose=CommunityPurpose.SERVICE,
        virtue_emphasis=virtue_emphasis,
        created_by=created_by,
        tool_ids=GRANT_GETTER_TOOLS,
    )

    # Register tools if requested
    if register_tools:
        _register_grant_tools()

    return community


def _register_grant_tools() -> None:
    """Register Grant-Getter tools in the tool registry."""
    tool_registry = get_tool_registry()

    # Only register if not already registered
    if not tool_registry.get("tool_grant_discovery"):
        tool_registry.register(GrantDiscovery())

    if not tool_registry.get("tool_proposal_writer"):
        tool_registry.register(ProposalWriter())

    if not tool_registry.get("tool_compliance_checker"):
        tool_registry.register(ComplianceChecker())

    if not tool_registry.get("tool_deadline_tracker"):
        tool_registry.register(DeadlineTracker())
