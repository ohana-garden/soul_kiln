"""
Skill definitions for the Student Financial Advocacy Platform.

Skills are organized by type: HARD, SOFT, DOMAIN, RITUAL.
"""

from src.models import Skill, SkillType

AMBASSADOR_SKILLS = {
    # HARD SKILLS - Concrete, measurable capabilities
    "S_DOC_PARSE": Skill(
        id="S_DOC_PARSE",
        name="Document Parsing",
        description="Extract structured data from tax documents, W-2s, 1040s, and financial statements.",
        skill_type=SkillType.HARD,
        domain="document_processing",
        mastery_floor=0.8,
        decay_rate=0.005,
        tool_id="document_parse_mcp",
    ),
    "S_FORM_COMPLETE": Skill(
        id="S_FORM_COMPLETE",
        name="Form Completion",
        description="Guide completion of FAFSA, CSS Profile, and institutional aid forms.",
        skill_type=SkillType.HARD,
        domain="financial_aid",
        mastery_floor=0.7,
        decay_rate=0.01,
        prerequisite_skills=["S_DOC_PARSE"],
        tool_id="fafsa_helper_mcp",
    ),
    "S_SCHOLARSHIP_SEARCH": Skill(
        id="S_SCHOLARSHIP_SEARCH",
        name="Scholarship Discovery",
        description="Search and match scholarships to student profiles.",
        skill_type=SkillType.HARD,
        domain="financial_aid",
        mastery_floor=0.6,
        decay_rate=0.02,
        tool_id="scholarship_search_mcp",
    ),
    "S_APPEAL_DRAFT": Skill(
        id="S_APPEAL_DRAFT",
        name="Appeal Letter Generation",
        description="Draft effective financial aid appeal letters.",
        skill_type=SkillType.HARD,
        domain="financial_aid",
        mastery_floor=0.5,
        decay_rate=0.02,
        prerequisite_skills=["S_SCHOLARSHIP_SEARCH"],
        tool_id="appeal_draft_mcp",
    ),
    "S_AID_CALC": Skill(
        id="S_AID_CALC",
        name="Aid Calculation",
        description="Calculate EFC, estimate aid packages, compare offers.",
        skill_type=SkillType.HARD,
        domain="financial_aid",
        mastery_floor=0.7,
        decay_rate=0.01,
        tool_id="aid_calculator_mcp",
    ),

    # SOFT SKILLS - Interpersonal capabilities
    "S_EMPATHY": Skill(
        id="S_EMPATHY",
        name="Empathetic Response",
        description="Detect and respond appropriately to emotional states.",
        skill_type=SkillType.SOFT,
        domain="relationship",
        mastery_floor=0.6,
        decay_rate=0.01,
        required_virtues=["V13", "V07"],  # Goodwill, Forbearance
    ),
    "S_ENCOURAGEMENT": Skill(
        id="S_ENCOURAGEMENT",
        name="Encouragement Calibration",
        description="Provide appropriate levels of encouragement and motivation.",
        skill_type=SkillType.SOFT,
        domain="relationship",
        mastery_floor=0.5,
        decay_rate=0.02,
        required_virtues=["V13", "V09"],  # Goodwill, Hospitality
    ),
    "S_ANXIETY_REDUCTION": Skill(
        id="S_ANXIETY_REDUCTION",
        name="Anxiety Mitigation",
        description="Calm anxious students, break tasks into manageable steps.",
        skill_type=SkillType.SOFT,
        domain="relationship",
        mastery_floor=0.5,
        decay_rate=0.02,
        prerequisite_skills=["S_EMPATHY"],
        required_virtues=["V07"],  # Forbearance
    ),

    # DOMAIN SKILLS - Specialized knowledge application
    "S_FAFSA_NAV": Skill(
        id="S_FAFSA_NAV",
        name="FAFSA Navigation",
        description="Expert knowledge of FAFSA process, edge cases, and strategies.",
        skill_type=SkillType.DOMAIN,
        domain="financial_aid",
        mastery_floor=0.7,
        decay_rate=0.01,
        prerequisite_knowledge=["fafsa_knowledge_domain"],
    ),
    "S_EFC_STRATEGY": Skill(
        id="S_EFC_STRATEGY",
        name="EFC Optimization",
        description="Strategies for legally minimizing Expected Family Contribution.",
        skill_type=SkillType.DOMAIN,
        domain="financial_aid",
        mastery_floor=0.6,
        decay_rate=0.02,
        prerequisite_skills=["S_FAFSA_NAV", "S_AID_CALC"],
    ),
    "S_APPEAL_STRATEGY": Skill(
        id="S_APPEAL_STRATEGY",
        name="Appeal Strategy",
        description="Develop effective appeal strategies based on institutional patterns.",
        skill_type=SkillType.DOMAIN,
        domain="financial_aid",
        mastery_floor=0.5,
        decay_rate=0.02,
        prerequisite_skills=["S_FAFSA_NAV"],
    ),

    # RITUAL SKILLS - Procedural sequences
    "S_DEADLINE_RITUAL": Skill(
        id="S_DEADLINE_RITUAL",
        name="Deadline Management Ritual",
        description="Systematic approach to tracking and meeting all deadlines.",
        skill_type=SkillType.RITUAL,
        domain="financial_aid",
        mastery_floor=0.8,
        decay_rate=0.005,
        tool_id="deadline_check_mcp",
    ),
    "S_NEGOTIATION_RITUAL": Skill(
        id="S_NEGOTIATION_RITUAL",
        name="Negotiation Protocol",
        description="Step-by-step negotiation process with schools.",
        skill_type=SkillType.RITUAL,
        domain="financial_aid",
        mastery_floor=0.5,
        decay_rate=0.02,
        prerequisite_skills=["S_APPEAL_STRATEGY", "S_EMPATHY"],
    ),
    "S_ONBOARDING_RITUAL": Skill(
        id="S_ONBOARDING_RITUAL",
        name="Student Onboarding",
        description="Systematic process for gathering student information and building trust.",
        skill_type=SkillType.RITUAL,
        domain="relationship",
        mastery_floor=0.7,
        decay_rate=0.01,
        prerequisite_skills=["S_EMPATHY"],
    ),
}


def get_skill_definition(skill_id: str) -> Skill | None:
    """Get a skill definition by ID."""
    return AMBASSADOR_SKILLS.get(skill_id)


def get_all_skill_ids() -> list[str]:
    """Get all skill IDs."""
    return list(AMBASSADOR_SKILLS.keys())


def get_skills_by_type(skill_type: SkillType) -> list[Skill]:
    """Get all skills of a specific type."""
    return [s for s in AMBASSADOR_SKILLS.values() if s.skill_type == skill_type]


def get_skills_by_domain(domain: str) -> list[Skill]:
    """Get all skills for a specific domain."""
    return [s for s in AMBASSADOR_SKILLS.values() if s.domain == domain]


def get_skills_requiring_virtue(virtue_id: str) -> list[Skill]:
    """Get all skills that require a specific virtue."""
    return [s for s in AMBASSADOR_SKILLS.values() if virtue_id in s.required_virtues]
