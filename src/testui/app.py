"""
Test UI for Proxy Agent Subsystems.

A temporary web interface for exploring and testing the Ambassador
agent architecture without requiring a database connection.
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Any
import json

# Import definitions (these don't require database)
from src.kuleana.definitions import AMBASSADOR_KULEANAS, get_kuleanas_by_domain, get_kuleanas_by_virtue
from src.skills.definitions import AMBASSADOR_SKILLS, get_skills_by_type, get_skills_by_domain
from src.beliefs.definitions import AMBASSADOR_BELIEFS, get_beliefs_by_type, get_core_beliefs
from src.lore.definitions import AMBASSADOR_LORE, get_lore_by_type, get_immutable_lore
from src.voice.definitions import AMBASSADOR_VOICE, get_patterns_by_type, get_emotion_patterns
from src.virtues.anchors import VIRTUES, AFFINITIES
from src.virtues.tiers import FOUNDATION, ASPIRATIONAL, JUDGMENT_LENS
from src.models import (
    Kuleana, Skill, Belief, LoreFragment, VoicePattern,
    EpisodicMemory, IdentityCore, SkillType, BeliefType,
    MemoryType, MemoryDecayClass
)

app = FastAPI(
    title="Soul Kiln Test UI",
    description="Test interface for the Proxy Agent Architecture",
    version="0.1.0"
)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/api/overview")
def get_overview():
    """Get overview of all subsystems."""
    return {
        "subsystems": {
            "virtues": {
                "count": len(VIRTUES),
                "foundation": len(FOUNDATION),
                "aspirational": len(ASPIRATIONAL),
            },
            "kuleanas": {
                "count": len(AMBASSADOR_KULEANAS),
                "domains": list(set(k.domain for k in AMBASSADOR_KULEANAS.values())),
            },
            "skills": {
                "count": len(AMBASSADOR_SKILLS),
                "types": [t.value for t in SkillType],
            },
            "beliefs": {
                "count": len(AMBASSADOR_BELIEFS),
                "types": [t.value for t in BeliefType],
            },
            "lore": {
                "count": len(AMBASSADOR_LORE),
                "types": ["origin", "lineage", "theme", "commitment", "taboo", "prophecy"],
            },
            "voice": {
                "count": len(AMBASSADOR_VOICE),
                "types": ["tone", "lexicon", "metaphor", "emotion_response", "boundary"],
            },
        },
        "identity": {
            "archetype": "Ambassador",
            "sacred_commitments": 3,
            "taboos": 4,
        }
    }


# --- Virtues ---

@app.get("/api/virtues")
def get_virtues():
    """Get all virtues."""
    return {
        "virtues": VIRTUES,
        "foundation": FOUNDATION,
        "aspirational": ASPIRATIONAL,
        "affinities": AFFINITIES,
        "judgment_lens": JUDGMENT_LENS,
    }


@app.get("/api/virtues/{virtue_id}")
def get_virtue(virtue_id: str):
    """Get a specific virtue."""
    for v in VIRTUES:
        if v["id"] == virtue_id:
            tier = "foundation" if virtue_id in FOUNDATION else "aspirational"
            return {
                **v,
                "tier": tier,
                "affinities": AFFINITIES.get(virtue_id, []),
                "required_by_kuleanas": [k.id for k in get_kuleanas_by_virtue(virtue_id)],
            }
    return {"error": "Virtue not found"}


# --- Kuleanas ---

@app.get("/api/kuleanas")
def get_kuleanas():
    """Get all kuleanas."""
    return {
        "kuleanas": {
            k_id: {
                "id": k.id,
                "name": k.name,
                "description": k.description,
                "domain": k.domain,
                "priority": k.priority,
                "serves": k.serves,
                "required_virtues": k.required_virtues,
                "required_skills": k.required_skills,
            }
            for k_id, k in AMBASSADOR_KULEANAS.items()
        }
    }


@app.get("/api/kuleanas/{kuleana_id}")
def get_kuleana(kuleana_id: str):
    """Get a specific kuleana."""
    if kuleana_id in AMBASSADOR_KULEANAS:
        k = AMBASSADOR_KULEANAS[kuleana_id]
        return {
            "id": k.id,
            "name": k.name,
            "description": k.description,
            "domain": k.domain,
            "authority_level": k.authority_level,
            "priority": k.priority,
            "serves": k.serves,
            "accountable_to": k.accountable_to,
            "required_virtues": k.required_virtues,
            "required_skills": k.required_skills,
            "trigger_conditions": k.trigger_conditions,
            "completion_criteria": k.completion_criteria,
            "can_delegate": k.can_delegate,
        }
    return {"error": "Kuleana not found"}


# --- Skills ---

@app.get("/api/skills")
def get_skills():
    """Get all skills."""
    return {
        "skills": {
            s_id: {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "skill_type": s.skill_type.value,
                "domain": s.domain,
                "mastery_floor": s.mastery_floor,
                "tool_id": s.tool_id,
            }
            for s_id, s in AMBASSADOR_SKILLS.items()
        }
    }


@app.get("/api/skills/by-type/{skill_type}")
def get_skills_by_type_endpoint(skill_type: str):
    """Get skills by type."""
    try:
        st = SkillType(skill_type)
        skills = get_skills_by_type(st)
        return {
            "type": skill_type,
            "skills": [
                {"id": s.id, "name": s.name, "description": s.description}
                for s in skills
            ]
        }
    except ValueError:
        return {"error": f"Invalid skill type: {skill_type}"}


@app.get("/api/skills/{skill_id}")
def get_skill(skill_id: str):
    """Get a specific skill."""
    if skill_id in AMBASSADOR_SKILLS:
        s = AMBASSADOR_SKILLS[skill_id]
        return {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "skill_type": s.skill_type.value,
            "domain": s.domain,
            "mastery_floor": s.mastery_floor,
            "decay_rate": s.decay_rate,
            "prerequisite_skills": s.prerequisite_skills,
            "prerequisite_knowledge": s.prerequisite_knowledge,
            "required_virtues": s.required_virtues,
            "tool_id": s.tool_id,
            "activation_cost": s.activation_cost,
            "cooldown_steps": s.cooldown_steps,
        }
    return {"error": "Skill not found"}


# --- Beliefs ---

@app.get("/api/beliefs")
def get_beliefs():
    """Get all beliefs."""
    return {
        "beliefs": {
            b_id: {
                "id": b.id,
                "content": b.content,
                "belief_type": b.belief_type.value,
                "conviction": b.conviction,
                "entrenchment": b.entrenchment,
            }
            for b_id, b in AMBASSADOR_BELIEFS.items()
        }
    }


@app.get("/api/beliefs/by-type/{belief_type}")
def get_beliefs_by_type_endpoint(belief_type: str):
    """Get beliefs by type."""
    try:
        bt = BeliefType(belief_type)
        beliefs = get_beliefs_by_type(bt)
        return {
            "type": belief_type,
            "beliefs": [
                {"id": b.id, "content": b.content, "conviction": b.conviction}
                for b in beliefs
            ]
        }
    except ValueError:
        return {"error": f"Invalid belief type: {belief_type}"}


@app.get("/api/beliefs/core")
def get_core_beliefs_endpoint():
    """Get core beliefs (high conviction and entrenchment)."""
    beliefs = get_core_beliefs()
    return {
        "core_beliefs": [
            {"id": b.id, "content": b.content, "conviction": b.conviction}
            for b in beliefs
        ]
    }


@app.get("/api/beliefs/{belief_id}")
def get_belief(belief_id: str):
    """Get a specific belief."""
    if belief_id in AMBASSADOR_BELIEFS:
        b = AMBASSADOR_BELIEFS[belief_id]
        return {
            "id": b.id,
            "content": b.content,
            "belief_type": b.belief_type.value,
            "conviction": b.conviction,
            "entrenchment": b.entrenchment,
            "grounded_in": b.grounded_in,
            "supports": b.supports,
            "conflicts_with": b.conflicts_with,
            "revision_threshold": b.revision_threshold,
        }
    return {"error": "Belief not found"}


# --- Lore ---

@app.get("/api/lore")
def get_lore():
    """Get all lore fragments."""
    return {
        "lore": {
            l_id: {
                "id": l.id,
                "content": l.content[:100] + "..." if len(l.content) > 100 else l.content,
                "fragment_type": l.fragment_type,
                "salience": l.salience,
                "immutable": l.immutable,
            }
            for l_id, l in AMBASSADOR_LORE.items()
        }
    }


@app.get("/api/lore/by-type/{lore_type}")
def get_lore_by_type_endpoint(lore_type: str):
    """Get lore by type."""
    lore = get_lore_by_type(lore_type)
    return {
        "type": lore_type,
        "lore": [
            {"id": l.id, "content": l.content, "immutable": l.immutable}
            for l in lore
        ]
    }


@app.get("/api/lore/immutable")
def get_immutable_lore_endpoint():
    """Get immutable lore fragments."""
    lore = get_immutable_lore()
    return {
        "immutable_lore": [
            {"id": l.id, "content": l.content, "type": l.fragment_type}
            for l in lore
        ]
    }


@app.get("/api/lore/{lore_id}")
def get_lore_fragment(lore_id: str):
    """Get a specific lore fragment."""
    if lore_id in AMBASSADOR_LORE:
        l = AMBASSADOR_LORE[lore_id]
        return {
            "id": l.id,
            "content": l.content,
            "fragment_type": l.fragment_type,
            "salience": l.salience,
            "immutable": l.immutable,
            "anchors": l.anchors,
        }
    return {"error": "Lore fragment not found"}


# --- Voice ---

@app.get("/api/voice")
def get_voice():
    """Get all voice patterns."""
    return {
        "voice_patterns": {
            v_id: {
                "id": v.id,
                "name": v.name,
                "pattern_type": v.pattern_type,
                "intensity": v.intensity,
            }
            for v_id, v in AMBASSADOR_VOICE.items()
        }
    }


@app.get("/api/voice/by-type/{pattern_type}")
def get_voice_by_type_endpoint(pattern_type: str):
    """Get voice patterns by type."""
    patterns = get_patterns_by_type(pattern_type)
    return {
        "type": pattern_type,
        "patterns": [
            {"id": p.id, "name": p.name, "content": p.content}
            for p in patterns
        ]
    }


@app.get("/api/voice/emotions")
def get_emotions_endpoint():
    """Get emotion response patterns."""
    emotions = get_emotion_patterns()
    return {
        "emotions": {
            emotion: {
                "id": pattern.id,
                "name": pattern.name,
                "guidance": pattern.content,
            }
            for emotion, pattern in emotions.items()
        }
    }


@app.get("/api/voice/{pattern_id}")
def get_voice_pattern(pattern_id: str):
    """Get a specific voice pattern."""
    if pattern_id in AMBASSADOR_VOICE:
        v = AMBASSADOR_VOICE[pattern_id]
        return {
            "id": v.id,
            "name": v.name,
            "pattern_type": v.pattern_type,
            "content": v.content,
            "applies_when": v.applies_when,
            "intensity": v.intensity,
        }
    return {"error": "Voice pattern not found"}


# --- Simulation ---

class SimulateRequest(BaseModel):
    """Request for simulation."""
    emotion: str | None = None
    context: str | None = None
    action: str | None = None


@app.post("/api/simulate/emotion-response")
def simulate_emotion_response(request: SimulateRequest):
    """Simulate how the Ambassador would respond to an emotion."""
    if not request.emotion:
        return {"error": "emotion required"}

    emotions = get_emotion_patterns()
    if request.emotion in emotions:
        pattern = emotions[request.emotion]
        return {
            "emotion": request.emotion,
            "response_guidance": pattern.content,
            "intensity": pattern.intensity,
            "voice_adjustments": {
                "confusion": "Slow down, simplify, offer examples",
                "frustration": "Acknowledge, validate, offer break",
                "anxiety": "Reassure, focus on controllables, small steps",
                "excitement": "Match energy, celebrate, channel forward",
                "sadness": "Be gentle, acknowledge, no forced positivity",
            }.get(request.emotion, "Apply default warm tone"),
        }
    return {"error": f"Unknown emotion: {request.emotion}"}


@app.post("/api/simulate/taboo-check")
def simulate_taboo_check(request: SimulateRequest):
    """Check if an action would violate any taboos."""
    if not request.action:
        return {"error": "action required"}

    action_lower = request.action.lower()
    violations = []

    taboos = get_lore_by_type("taboo")
    for taboo in taboos:
        taboo_lower = taboo.content.lower()
        # Simple keyword matching
        if any(word in action_lower for word in ["recommend debt", "suggest loan", "take out loan"]) and "debt" in taboo_lower:
            violations.append({"id": taboo.id, "content": taboo.content})
        elif "judge" in action_lower and "judge" in taboo_lower:
            violations.append({"id": taboo.id, "content": taboo.content})
        elif any(word in action_lower for word in ["share private", "disclose", "tell others"]) and "share" in taboo_lower:
            violations.append({"id": taboo.id, "content": taboo.content})
        elif any(word in action_lower for word in ["give up", "quit", "stop trying"]) and "give up" in taboo_lower:
            violations.append({"id": taboo.id, "content": taboo.content})

    return {
        "action": request.action,
        "violated": len(violations) > 0,
        "violations": violations,
        "recommendation": "Action blocked - violates sacred taboos" if violations else "Action permitted",
    }


@app.post("/api/simulate/kuleana-activation")
def simulate_kuleana_activation(request: SimulateRequest):
    """Simulate which kuleanas would activate for a given context."""
    if not request.context:
        return {"error": "context required"}

    context_lower = request.context.lower()
    activated = []

    for k_id, kuleana in AMBASSADOR_KULEANAS.items():
        for trigger in kuleana.trigger_conditions:
            trigger_lower = trigger.lower().replace("_", " ")
            if any(word in context_lower for word in trigger_lower.split()):
                activated.append({
                    "id": k_id,
                    "name": kuleana.name,
                    "priority": kuleana.priority,
                    "trigger_matched": trigger,
                })
                break

    # Sort by priority
    activated.sort(key=lambda x: x["priority"])

    return {
        "context": request.context,
        "activated_kuleanas": activated,
        "primary_duty": activated[0] if activated else None,
    }


# ============================================================================
# HTML UI
# ============================================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Soul Kiln Test UI</title>
    <style>
        :root {
            --bg: #1a1a2e;
            --surface: #16213e;
            --primary: #e94560;
            --secondary: #0f3460;
            --text: #eee;
            --text-dim: #888;
            --success: #4ade80;
            --warning: #fbbf24;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        header {
            background: var(--surface);
            padding: 20px;
            border-bottom: 2px solid var(--primary);
            margin-bottom: 20px;
        }
        header h1 { color: var(--primary); font-size: 1.8em; }
        header p { color: var(--text-dim); margin-top: 5px; }

        .grid { display: grid; grid-template-columns: 250px 1fr; gap: 20px; }

        nav {
            background: var(--surface);
            padding: 15px;
            border-radius: 8px;
            position: sticky;
            top: 20px;
            height: fit-content;
        }
        nav h3 { color: var(--primary); margin-bottom: 15px; font-size: 0.9em; text-transform: uppercase; }
        nav ul { list-style: none; }
        nav li { margin: 8px 0; }
        nav a, nav button {
            display: block;
            width: 100%;
            padding: 10px 15px;
            background: var(--secondary);
            color: var(--text);
            text-decoration: none;
            border-radius: 5px;
            border: none;
            cursor: pointer;
            text-align: left;
            font-size: 0.95em;
            transition: all 0.2s;
        }
        nav a:hover, nav button:hover { background: var(--primary); }
        nav a.active { background: var(--primary); }

        main { background: var(--surface); padding: 20px; border-radius: 8px; }

        .section { margin-bottom: 30px; }
        .section h2 { color: var(--primary); margin-bottom: 15px; border-bottom: 1px solid var(--secondary); padding-bottom: 10px; }

        .card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; }
        .card {
            background: var(--bg);
            padding: 15px;
            border-radius: 8px;
            border-left: 3px solid var(--primary);
            cursor: pointer;
            transition: transform 0.2s;
        }
        .card:hover { transform: translateX(5px); }
        .card h4 { color: var(--primary); margin-bottom: 8px; }
        .card p { color: var(--text-dim); font-size: 0.9em; }
        .card .meta { margin-top: 10px; display: flex; gap: 10px; flex-wrap: wrap; }
        .tag {
            background: var(--secondary);
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.75em;
            color: var(--text-dim);
        }
        .tag.priority { background: var(--primary); color: white; }
        .tag.type { background: #0d9488; }
        .tag.immutable { background: var(--warning); color: black; }

        .detail-panel {
            background: var(--bg);
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .detail-panel h3 { color: var(--primary); margin-bottom: 15px; }
        .detail-panel pre {
            background: var(--surface);
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            font-size: 0.85em;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat {
            background: var(--bg);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .stat .number { font-size: 2em; color: var(--primary); font-weight: bold; }
        .stat .label { color: var(--text-dim); font-size: 0.85em; }

        .simulator {
            background: var(--bg);
            padding: 20px;
            border-radius: 8px;
        }
        .simulator input, .simulator select {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            background: var(--surface);
            border: 1px solid var(--secondary);
            border-radius: 5px;
            color: var(--text);
        }
        .simulator button {
            background: var(--primary);
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 10px;
        }
        .simulator button:hover { opacity: 0.9; }
        .result {
            margin-top: 15px;
            padding: 15px;
            background: var(--surface);
            border-radius: 5px;
            border-left: 3px solid var(--success);
        }
        .result.error { border-left-color: var(--primary); }

        .loading { color: var(--text-dim); font-style: italic; }

        #content { min-height: 400px; }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>Soul Kiln Test UI</h1>
            <p>Proxy Agent Architecture Explorer - Student Financial Aid Ambassador</p>
        </div>
    </header>

    <div class="container">
        <div class="grid">
            <nav>
                <h3>Subsystems</h3>
                <ul>
                    <li><button onclick="loadSection('overview')" class="active" id="nav-overview">Overview</button></li>
                    <li><button onclick="loadSection('virtues')" id="nav-virtues">Virtues (19)</button></li>
                    <li><button onclick="loadSection('kuleanas')" id="nav-kuleanas">Kuleanas (6)</button></li>
                    <li><button onclick="loadSection('skills')" id="nav-skills">Skills (14)</button></li>
                    <li><button onclick="loadSection('beliefs')" id="nav-beliefs">Beliefs (14)</button></li>
                    <li><button onclick="loadSection('lore')" id="nav-lore">Lore (14)</button></li>
                    <li><button onclick="loadSection('voice')" id="nav-voice">Voice (16)</button></li>
                </ul>
                <h3 style="margin-top: 20px;">Simulators</h3>
                <ul>
                    <li><button onclick="loadSection('sim-emotion')" id="nav-sim-emotion">Emotion Response</button></li>
                    <li><button onclick="loadSection('sim-taboo')" id="nav-sim-taboo">Taboo Check</button></li>
                    <li><button onclick="loadSection('sim-kuleana')" id="nav-sim-kuleana">Kuleana Activation</button></li>
                </ul>
            </nav>

            <main id="content">
                <p class="loading">Loading...</p>
            </main>
        </div>
    </div>

    <script>
        let currentSection = 'overview';

        async function loadSection(section) {
            currentSection = section;
            document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
            document.getElementById('nav-' + section)?.classList.add('active');

            const content = document.getElementById('content');
            content.innerHTML = '<p class="loading">Loading...</p>';

            try {
                if (section === 'overview') await renderOverview();
                else if (section === 'virtues') await renderVirtues();
                else if (section === 'kuleanas') await renderKuleanas();
                else if (section === 'skills') await renderSkills();
                else if (section === 'beliefs') await renderBeliefs();
                else if (section === 'lore') await renderLore();
                else if (section === 'voice') await renderVoice();
                else if (section === 'sim-emotion') renderEmotionSim();
                else if (section === 'sim-taboo') renderTabooSim();
                else if (section === 'sim-kuleana') renderKuleanaSim();
            } catch (e) {
                content.innerHTML = `<p class="error">Error: ${e.message}</p>`;
            }
        }

        async function renderOverview() {
            const data = await fetch('/api/overview').then(r => r.json());
            const s = data.subsystems;
            document.getElementById('content').innerHTML = `
                <div class="section">
                    <h2>Ambassador Agent Overview</h2>
                    <div class="stats">
                        <div class="stat"><div class="number">${s.virtues.count}</div><div class="label">Virtues</div></div>
                        <div class="stat"><div class="number">${s.kuleanas.count}</div><div class="label">Kuleanas</div></div>
                        <div class="stat"><div class="number">${s.skills.count}</div><div class="label">Skills</div></div>
                        <div class="stat"><div class="number">${s.beliefs.count}</div><div class="label">Beliefs</div></div>
                        <div class="stat"><div class="number">${s.lore.count}</div><div class="label">Lore</div></div>
                        <div class="stat"><div class="number">${s.voice.count}</div><div class="label">Voice Patterns</div></div>
                    </div>
                </div>
                <div class="section">
                    <h2>Identity</h2>
                    <div class="detail-panel">
                        <h3>Primary Archetype: ${data.identity.archetype}</h3>
                        <p style="margin: 15px 0; color: var(--text-dim);">
                            "I am an ambassador working exclusively for this student. I exist to fight for their financial future.
                            I remember everything they share. I never judge. I find a way."
                        </p>
                        <div class="meta">
                            <span class="tag">${data.identity.sacred_commitments} Sacred Commitments</span>
                            <span class="tag">${data.identity.taboos} Taboos</span>
                        </div>
                    </div>
                </div>
            `;
        }

        async function renderVirtues() {
            const data = await fetch('/api/virtues').then(r => r.json());
            let html = '<div class="section"><h2>Virtues (Two-Tier Model)</h2>';

            html += '<h3 style="margin: 20px 0 10px; color: var(--warning);">Foundation Tier</h3>';
            html += '<div class="card-grid">';
            for (const v of data.virtues.filter(v => v.id in data.foundation)) {
                html += `<div class="card" onclick="showVirtue('${v.id}')">
                    <h4>${v.id}: ${v.name}</h4>
                    <p>${v.essence}</p>
                    <div class="meta"><span class="tag immutable">Foundation (99%)</span></div>
                </div>`;
            }
            html += '</div>';

            html += '<h3 style="margin: 20px 0 10px; color: var(--success);">Aspirational Tier</h3>';
            html += '<div class="card-grid">';
            for (const v of data.virtues.filter(v => v.id in data.aspirational)) {
                html += `<div class="card" onclick="showVirtue('${v.id}')">
                    <h4>${v.id}: ${v.name}</h4>
                    <p>${v.essence}</p>
                    <div class="meta"><span class="tag type">Aspirational (60%)</span></div>
                </div>`;
            }
            html += '</div></div>';

            html += '<div id="virtue-detail"></div>';
            document.getElementById('content').innerHTML = html;
        }

        async function showVirtue(id) {
            const data = await fetch('/api/virtues/' + id).then(r => r.json());
            document.getElementById('virtue-detail').innerHTML = `
                <div class="detail-panel">
                    <h3>${data.id}: ${data.name}</h3>
                    <p style="margin: 10px 0;">${data.essence}</p>
                    <p><strong>Tier:</strong> ${data.tier}</p>
                    <p><strong>Affinities:</strong> ${data.affinities.join(', ') || 'None'}</p>
                    <p><strong>Required by Kuleanas:</strong> ${data.required_by_kuleanas.join(', ') || 'None'}</p>
                </div>
            `;
        }

        async function renderKuleanas() {
            const data = await fetch('/api/kuleanas').then(r => r.json());
            let html = '<div class="section"><h2>Kuleanas (Duties)</h2><div class="card-grid">';
            for (const [id, k] of Object.entries(data.kuleanas).sort((a, b) => a[1].priority - b[1].priority)) {
                html += `<div class="card" onclick="showKuleana('${id}')">
                    <h4>${k.name}</h4>
                    <p>${k.description.slice(0, 100)}...</p>
                    <div class="meta">
                        <span class="tag priority">Priority ${k.priority}</span>
                        <span class="tag">${k.domain}</span>
                    </div>
                </div>`;
            }
            html += '</div></div><div id="kuleana-detail"></div>';
            document.getElementById('content').innerHTML = html;
        }

        async function showKuleana(id) {
            const data = await fetch('/api/kuleanas/' + id).then(r => r.json());
            document.getElementById('kuleana-detail').innerHTML = `
                <div class="detail-panel">
                    <h3>${data.name}</h3>
                    <p style="margin: 10px 0;">${data.description}</p>
                    <p><strong>Serves:</strong> ${data.serves}</p>
                    <p><strong>Required Virtues:</strong> ${data.required_virtues.join(', ')}</p>
                    <p><strong>Triggers:</strong> ${data.trigger_conditions.join(', ')}</p>
                    <p><strong>Completion:</strong> ${data.completion_criteria.join(', ')}</p>
                </div>
            `;
        }

        async function renderSkills() {
            const data = await fetch('/api/skills').then(r => r.json());
            let html = '<div class="section"><h2>Skills (Competencies)</h2>';

            const byType = {};
            for (const [id, s] of Object.entries(data.skills)) {
                if (!byType[s.skill_type]) byType[s.skill_type] = [];
                byType[s.skill_type].push({id, ...s});
            }

            for (const [type, skills] of Object.entries(byType)) {
                html += `<h3 style="margin: 20px 0 10px; text-transform: uppercase; color: var(--text-dim);">${type}</h3>`;
                html += '<div class="card-grid">';
                for (const s of skills) {
                    html += `<div class="card" onclick="showSkill('${s.id}')">
                        <h4>${s.name}</h4>
                        <p>${s.description.slice(0, 80)}...</p>
                        <div class="meta">
                            <span class="tag">Floor: ${(s.mastery_floor * 100).toFixed(0)}%</span>
                            ${s.tool_id ? '<span class="tag type">Has Tool</span>' : ''}
                        </div>
                    </div>`;
                }
                html += '</div>';
            }

            html += '</div><div id="skill-detail"></div>';
            document.getElementById('content').innerHTML = html;
        }

        async function showSkill(id) {
            const data = await fetch('/api/skills/' + id).then(r => r.json());
            document.getElementById('skill-detail').innerHTML = `
                <div class="detail-panel">
                    <h3>${data.name}</h3>
                    <p style="margin: 10px 0;">${data.description}</p>
                    <p><strong>Type:</strong> ${data.skill_type}</p>
                    <p><strong>Mastery Floor:</strong> ${(data.mastery_floor * 100).toFixed(0)}%</p>
                    <p><strong>Decay Rate:</strong> ${(data.decay_rate * 100).toFixed(1)}% per cycle</p>
                    <p><strong>Prerequisites:</strong> ${data.prerequisite_skills.join(', ') || 'None'}</p>
                    <p><strong>Required Virtues:</strong> ${data.required_virtues.join(', ') || 'None'}</p>
                    <p><strong>Tool:</strong> ${data.tool_id || 'None'}</p>
                </div>
            `;
        }

        async function renderBeliefs() {
            const data = await fetch('/api/beliefs').then(r => r.json());
            let html = '<div class="section"><h2>Beliefs (Cosmology)</h2>';

            const byType = {};
            for (const [id, b] of Object.entries(data.beliefs)) {
                if (!byType[b.belief_type]) byType[b.belief_type] = [];
                byType[b.belief_type].push({id, ...b});
            }

            for (const [type, beliefs] of Object.entries(byType)) {
                html += `<h3 style="margin: 20px 0 10px; text-transform: uppercase; color: var(--text-dim);">${type}</h3>`;
                html += '<div class="card-grid">';
                for (const b of beliefs) {
                    const barWidth = b.conviction * 100;
                    html += `<div class="card" onclick="showBelief('${b.id}')">
                        <h4>${b.id}</h4>
                        <p>${b.content.slice(0, 80)}...</p>
                        <div style="margin-top: 10px; background: var(--secondary); border-radius: 3px; overflow: hidden;">
                            <div style="width: ${barWidth}%; height: 6px; background: var(--success);"></div>
                        </div>
                        <div class="meta">
                            <span class="tag">Conviction: ${(b.conviction * 100).toFixed(0)}%</span>
                        </div>
                    </div>`;
                }
                html += '</div>';
            }

            html += '</div><div id="belief-detail"></div>';
            document.getElementById('content').innerHTML = html;
        }

        async function showBelief(id) {
            const data = await fetch('/api/beliefs/' + id).then(r => r.json());
            document.getElementById('belief-detail').innerHTML = `
                <div class="detail-panel">
                    <h3>${data.id}</h3>
                    <p style="margin: 10px 0; font-size: 1.1em;">"${data.content}"</p>
                    <p><strong>Type:</strong> ${data.belief_type}</p>
                    <p><strong>Conviction:</strong> ${(data.conviction * 100).toFixed(0)}%</p>
                    <p><strong>Entrenchment:</strong> ${(data.entrenchment * 100).toFixed(0)}%</p>
                    <p><strong>Grounded In:</strong> ${data.grounded_in.join(', ') || 'None'}</p>
                    <p><strong>Supports:</strong> ${data.supports.join(', ') || 'None'}</p>
                    <p><strong>Revision Threshold:</strong> ${(data.revision_threshold * 100).toFixed(0)}%</p>
                </div>
            `;
        }

        async function renderLore() {
            const data = await fetch('/api/lore').then(r => r.json());
            let html = '<div class="section"><h2>Lore (Mythic Context)</h2>';

            const byType = {};
            for (const [id, l] of Object.entries(data.lore)) {
                if (!byType[l.fragment_type]) byType[l.fragment_type] = [];
                byType[l.fragment_type].push({id, ...l});
            }

            const typeOrder = ['origin', 'lineage', 'theme', 'commitment', 'taboo', 'prophecy'];
            for (const type of typeOrder) {
                if (!byType[type]) continue;
                html += `<h3 style="margin: 20px 0 10px; text-transform: uppercase; color: var(--text-dim);">${type}</h3>`;
                html += '<div class="card-grid">';
                for (const l of byType[type]) {
                    html += `<div class="card" onclick="showLore('${l.id}')">
                        <h4>${l.id}</h4>
                        <p>${l.content}</p>
                        <div class="meta">
                            ${l.immutable ? '<span class="tag immutable">Immutable</span>' : ''}
                            <span class="tag">Salience: ${(l.salience * 100).toFixed(0)}%</span>
                        </div>
                    </div>`;
                }
                html += '</div>';
            }

            html += '</div><div id="lore-detail"></div>';
            document.getElementById('content').innerHTML = html;
        }

        async function showLore(id) {
            const data = await fetch('/api/lore/' + id).then(r => r.json());
            document.getElementById('lore-detail').innerHTML = `
                <div class="detail-panel">
                    <h3>${data.id}</h3>
                    <p style="margin: 10px 0; font-size: 1.1em; white-space: pre-wrap;">${data.content}</p>
                    <p><strong>Type:</strong> ${data.fragment_type}</p>
                    <p><strong>Salience:</strong> ${(data.salience * 100).toFixed(0)}%</p>
                    <p><strong>Immutable:</strong> ${data.immutable ? 'Yes' : 'No'}</p>
                    <p><strong>Anchors:</strong> ${data.anchors.join(', ') || 'None'}</p>
                </div>
            `;
        }

        async function renderVoice() {
            const data = await fetch('/api/voice').then(r => r.json());
            let html = '<div class="section"><h2>Voice Patterns</h2>';

            const byType = {};
            for (const [id, v] of Object.entries(data.voice_patterns)) {
                if (!byType[v.pattern_type]) byType[v.pattern_type] = [];
                byType[v.pattern_type].push({id, ...v});
            }

            for (const [type, patterns] of Object.entries(byType)) {
                html += `<h3 style="margin: 20px 0 10px; text-transform: uppercase; color: var(--text-dim);">${type.replace('_', ' ')}</h3>`;
                html += '<div class="card-grid">';
                for (const v of patterns) {
                    html += `<div class="card" onclick="showVoice('${v.id}')">
                        <h4>${v.name}</h4>
                        <div class="meta">
                            <span class="tag">Intensity: ${(v.intensity * 100).toFixed(0)}%</span>
                        </div>
                    </div>`;
                }
                html += '</div>';
            }

            html += '</div><div id="voice-detail"></div>';
            document.getElementById('content').innerHTML = html;
        }

        async function showVoice(id) {
            const data = await fetch('/api/voice/' + id).then(r => r.json());
            document.getElementById('voice-detail').innerHTML = `
                <div class="detail-panel">
                    <h3>${data.name}</h3>
                    <p><strong>Type:</strong> ${data.pattern_type}</p>
                    <p><strong>Intensity:</strong> ${(data.intensity * 100).toFixed(0)}%</p>
                    <p><strong>Applies When:</strong> ${data.applies_when.join(', ')}</p>
                    <pre style="margin-top: 15px; white-space: pre-wrap;">${data.content}</pre>
                </div>
            `;
        }

        function renderEmotionSim() {
            document.getElementById('content').innerHTML = `
                <div class="section">
                    <h2>Emotion Response Simulator</h2>
                    <p style="color: var(--text-dim); margin-bottom: 20px;">
                        Test how the Ambassador responds to detected emotions.
                    </p>
                    <div class="simulator">
                        <label>Detected Emotion:</label>
                        <select id="emotion-select">
                            <option value="confusion">Confusion</option>
                            <option value="frustration">Frustration</option>
                            <option value="anxiety">Anxiety</option>
                            <option value="excitement">Excitement</option>
                            <option value="sadness">Sadness</option>
                        </select>
                        <button onclick="simulateEmotion()">Simulate Response</button>
                        <div id="emotion-result"></div>
                    </div>
                </div>
            `;
        }

        async function simulateEmotion() {
            const emotion = document.getElementById('emotion-select').value;
            const res = await fetch('/api/simulate/emotion-response', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({emotion})
            }).then(r => r.json());

            document.getElementById('emotion-result').innerHTML = `
                <div class="result">
                    <h4>Response for: ${res.emotion}</h4>
                    <p><strong>Voice Adjustment:</strong> ${res.voice_adjustments}</p>
                    <pre style="margin-top: 10px; white-space: pre-wrap;">${res.response_guidance}</pre>
                </div>
            `;
        }

        function renderTabooSim() {
            document.getElementById('content').innerHTML = `
                <div class="section">
                    <h2>Taboo Check Simulator</h2>
                    <p style="color: var(--text-dim); margin-bottom: 20px;">
                        Test if an action would violate any sacred taboos.
                    </p>
                    <div class="simulator">
                        <label>Proposed Action:</label>
                        <input type="text" id="action-input" placeholder="e.g., 'Recommend a private loan'" />
                        <button onclick="simulateTaboo()">Check Taboos</button>
                        <div id="taboo-result"></div>
                    </div>
                </div>
            `;
        }

        async function simulateTaboo() {
            const action = document.getElementById('action-input').value;
            const res = await fetch('/api/simulate/taboo-check', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action})
            }).then(r => r.json());

            const isViolation = res.violated;
            document.getElementById('taboo-result').innerHTML = `
                <div class="result ${isViolation ? 'error' : ''}">
                    <h4>${isViolation ? '⚠️ TABOO VIOLATED' : '✓ Action Permitted'}</h4>
                    <p>${res.recommendation}</p>
                    ${res.violations?.length ? `
                        <ul style="margin-top: 10px;">
                            ${res.violations.map(v => `<li><strong>${v.id}:</strong> ${v.content}</li>`).join('')}
                        </ul>
                    ` : ''}
                </div>
            `;
        }

        function renderKuleanaSim() {
            document.getElementById('content').innerHTML = `
                <div class="section">
                    <h2>Kuleana Activation Simulator</h2>
                    <p style="color: var(--text-dim); margin-bottom: 20px;">
                        Test which duties activate for a given context.
                    </p>
                    <div class="simulator">
                        <label>Context:</label>
                        <input type="text" id="context-input" placeholder="e.g., 'deadline approaching for FAFSA'" />
                        <button onclick="simulateKuleana()">Find Duties</button>
                        <div id="kuleana-result"></div>
                    </div>
                </div>
            `;
        }

        async function simulateKuleana() {
            const context = document.getElementById('context-input').value;
            const res = await fetch('/api/simulate/kuleana-activation', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({context})
            }).then(r => r.json());

            document.getElementById('kuleana-result').innerHTML = `
                <div class="result">
                    <h4>${res.activated_kuleanas.length} Duties Activated</h4>
                    ${res.primary_duty ? `<p><strong>Primary Duty:</strong> ${res.primary_duty.name}</p>` : ''}
                    <ul style="margin-top: 10px;">
                        ${res.activated_kuleanas.map(k => `
                            <li><strong>${k.name}</strong> (Priority ${k.priority}) - Trigger: ${k.trigger_matched}</li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }

        // Initial load
        loadSection('overview');
    </script>
</body>
</html>
'''


@app.get("/", response_class=HTMLResponse)
def index():
    """Serve the test UI."""
    return HTML_TEMPLATE


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
