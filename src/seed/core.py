"""
Core Seed Data.

Seeds fundamental data structures used across all agent types.
"""
from datetime import datetime
from src.graph import get_client


def seed_core_data():
    """Seed core data structures."""
    client = get_client()
    now = datetime.utcnow().isoformat()

    # Seed core virtues that apply to all agents
    _seed_core_virtues(client, now)

    # Seed core taboo categories
    _seed_taboo_categories(client, now)

    # Seed financial aid types (domain-specific)
    _seed_financial_aid_types(client, now)

    print("Core seed data complete.")


def _seed_core_virtues(client, now: str):
    """Seed universal virtue anchors."""
    virtues = [
        {
            "id": "virtue-honesty",
            "name": "Honesty",
            "description": "Always provide truthful, accurate information",
            "keywords": "truth,accurate,honest,transparent,truthful",
        },
        {
            "id": "virtue-advocacy",
            "name": "Advocacy",
            "description": "Actively advocate for the student's best interests",
            "keywords": "advocate,support,help,assist,champion",
        },
        {
            "id": "virtue-empathy",
            "name": "Empathy",
            "description": "Understand and acknowledge the student's situation",
            "keywords": "understand,listen,acknowledge,compassion,care",
        },
        {
            "id": "virtue-diligence",
            "name": "Diligence",
            "description": "Thoroughly research and verify all information",
            "keywords": "thorough,verify,research,careful,meticulous",
        },
        {
            "id": "virtue-respect",
            "name": "Respect",
            "description": "Treat all parties with dignity and respect",
            "keywords": "dignity,respect,polite,courteous,professional",
        },
    ]

    for v in virtues:
        query = """
        MERGE (v:Virtue {id: $id})
        ON CREATE SET
            v.name = $name,
            v.description = $description,
            v.keywords = $keywords,
            v.created_at = datetime($now)
        ON MATCH SET
            v.name = $name,
            v.description = $description,
            v.keywords = $keywords
        """
        client.execute(query, {**v, "now": now})


def _seed_taboo_categories(client, now: str):
    """Seed taboo categories."""
    categories = [
        {
            "id": "taboo-cat-deception",
            "name": "Deception",
            "description": "Actions involving dishonesty or misleading information",
        },
        {
            "id": "taboo-cat-harm",
            "name": "Harm",
            "description": "Actions that could harm the student's interests",
        },
        {
            "id": "taboo-cat-bias",
            "name": "Bias",
            "description": "Actions showing unfair bias or discrimination",
        },
        {
            "id": "taboo-cat-privacy",
            "name": "Privacy",
            "description": "Actions violating privacy or data protection",
        },
    ]

    for cat in categories:
        query = """
        MERGE (tc:TabooCategory {id: $id})
        ON CREATE SET
            tc.name = $name,
            tc.description = $description,
            tc.created_at = datetime($now)
        """
        client.execute(query, {**cat, "now": now})


def _seed_financial_aid_types(client, now: str):
    """Seed financial aid type reference data."""
    aid_types = [
        {
            "id": "aid-federal-pell",
            "name": "Federal Pell Grant",
            "description": "Need-based federal grant for undergraduate students",
            "category": "grant",
            "federal": True,
        },
        {
            "id": "aid-federal-seog",
            "name": "Federal SEOG",
            "description": "Supplemental Educational Opportunity Grant",
            "category": "grant",
            "federal": True,
        },
        {
            "id": "aid-federal-work-study",
            "name": "Federal Work-Study",
            "description": "Part-time employment program for students with financial need",
            "category": "employment",
            "federal": True,
        },
        {
            "id": "aid-direct-subsidized",
            "name": "Direct Subsidized Loan",
            "description": "Federal loan where government pays interest while in school",
            "category": "loan",
            "federal": True,
        },
        {
            "id": "aid-direct-unsubsidized",
            "name": "Direct Unsubsidized Loan",
            "description": "Federal loan available regardless of financial need",
            "category": "loan",
            "federal": True,
        },
        {
            "id": "aid-plus-loan",
            "name": "PLUS Loan",
            "description": "Federal loan for parents or graduate students",
            "category": "loan",
            "federal": True,
        },
        {
            "id": "aid-state-grant",
            "name": "State Grant",
            "description": "Grant program administered by state agencies",
            "category": "grant",
            "federal": False,
        },
        {
            "id": "aid-institutional-grant",
            "name": "Institutional Grant",
            "description": "Grant provided directly by the educational institution",
            "category": "grant",
            "federal": False,
        },
        {
            "id": "aid-scholarship",
            "name": "Merit Scholarship",
            "description": "Awards based on academic or other achievements",
            "category": "scholarship",
            "federal": False,
        },
    ]

    for aid in aid_types:
        query = """
        MERGE (a:FinancialAidType {id: $id})
        ON CREATE SET
            a.name = $name,
            a.description = $description,
            a.category = $category,
            a.federal = $federal,
            a.created_at = datetime($now)
        ON MATCH SET
            a.name = $name,
            a.description = $description,
            a.category = $category,
            a.federal = $federal
        """
        client.execute(query, {**aid, "now": now})


if __name__ == "__main__":
    seed_core_data()
