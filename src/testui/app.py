"""
Soul Kiln API Server.

Production-ready API for the Graph-Based Proxy Agent Architecture.
All agent definitions loaded from FalkorDB graph.
"""
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from src.settings import settings
from src.graph import get_client, is_using_mock
from src.graph.schema import init_schema
from src.runtime import GraphAgentFactory, get_bridge

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Track startup time for health checks
_startup_time: Optional[datetime] = None
_is_ready: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global _startup_time, _is_ready

    # Startup
    _startup_time = datetime.utcnow()
    logger.info(f"Starting Soul Kiln API (env={settings.environment})")

    client = get_client()
    if client.is_mock:
        logger.info("Mock mode detected, auto-seeding data...")
        init_schema()
        from src.seed.core import seed_core_data
        from src.seed.ambassador import seed_ambassador
        seed_core_data()
        seed_ambassador()
        logger.info("Mock data seeded successfully")

    _is_ready = True
    logger.info(f"Soul Kiln API ready on {settings.api.host}:{settings.api.port}")

    yield

    # Shutdown
    logger.info("Shutting down Soul Kiln API")
    _is_ready = False


app = FastAPI(
    title="Soul Kiln API",
    description="Graph-Based Proxy Agent Architecture for Student Financial Advocacy",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Request logging middleware
# =============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing."""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s"
    )
    return response


# =============================================================================
# Global exception handler
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": str(exc) if settings.is_development else "An internal error occurred",
        }
    )


# =============================================================================
# Health & Readiness Endpoints
# =============================================================================

@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint for load balancers and container orchestration.
    Returns 200 if the service is running.
    """
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.environment,
        "uptime_seconds": (datetime.utcnow() - _startup_time).total_seconds() if _startup_time else 0,
    }


@app.get("/ready", tags=["Health"])
def readiness_check():
    """
    Readiness check endpoint. Returns 200 if the service is ready to accept traffic.
    Checks database connectivity.
    """
    if not _is_ready:
        raise HTTPException(status_code=503, detail="Service not ready")

    client = get_client()
    db_status = "mock" if client.is_mock else "connected"

    # Test database connection
    try:
        if not client.is_mock:
            client.query("RETURN 1")
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database unavailable: {e}")

    return {
        "ready": True,
        "database": db_status,
        "llm_configured": settings.llm.is_configured,
    }


@app.get("/api/config", tags=["Health"])
def get_config():
    """Get current configuration (non-sensitive values only)."""
    return {
        "environment": settings.environment,
        "database": {
            "host": settings.database.host,
            "port": settings.database.port,
            "graph": settings.database.graph,
        },
        "llm": {
            "model": settings.llm.model,
            "max_tokens": settings.llm.max_tokens,
            "configured": settings.llm.is_configured,
        },
    }


# =============================================================================
# API Key Authentication
# =============================================================================

from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Depends(api_key_header)) -> bool:
    """
    Verify API key for protected endpoints.
    In development mode, authentication is optional.
    In production, a valid API key is required.
    """
    if settings.is_development:
        # Development mode - auth is optional
        return True

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Set X-API-Key header.",
        )

    # Compare with configured secret key
    if api_key != settings.api.secret_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key",
        )

    return True


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/api/overview")
def get_overview():
    """Get overview of all data in the graph."""
    client = get_client()

    def count_nodes(label: str) -> int:
        try:
            result = client.query(f"MATCH (n:{label}) RETURN count(n) as c")
            return result[0][0] if result else 0
        except Exception:
            return 0

    return {
        "subsystems": {
            "agent_types": count_nodes("AgentType"),
            "agent_instances": count_nodes("AgentInstance"),
            "virtues": count_nodes("Virtue"),
            "kuleanas": count_nodes("Kuleana"),
            "beliefs": count_nodes("Belief"),
            "taboos": count_nodes("Taboo"),
            "lore": count_nodes("Lore"),
            "voice_patterns": count_nodes("VoicePattern"),
            "prompts": count_nodes("Prompt"),
            "tools": count_nodes("Tool"),
        },
        "graph_status": "connected",
    }


@app.get("/api/agent-types")
def get_agent_types():
    """Get all agent types."""
    client = get_client()
    query = """
    MATCH (t:AgentType)
    RETURN t
    ORDER BY t.name
    """
    result = client.query(query)
    return {
        "agent_types": [dict(row[0].properties) for row in result if row[0]]
    }


@app.get("/api/agent-types/{type_id}")
def get_agent_type(type_id: str):
    """Get detailed info about an agent type."""
    client = get_client()

    # Get type info
    query = "MATCH (t:AgentType {id: $id}) RETURN t"
    result = client.query(query, {"id": type_id})
    if not result:
        return {"error": "Agent type not found"}

    agent_type = dict(result[0][0].properties)

    # Get related data
    virtues_q = """
    MATCH (t:AgentType {id: $id})-[r:HAS_VIRTUE]->(v:Virtue)
    RETURN v, r.priority as priority
    ORDER BY r.priority DESC
    """
    virtues = client.query(virtues_q, {"id": type_id})

    kuleanas_q = """
    MATCH (t:AgentType {id: $id})-[r:HAS_KULEANA]->(k:Kuleana)
    RETURN k, r.priority as priority
    ORDER BY r.priority DESC
    """
    kuleanas = client.query(kuleanas_q, {"id": type_id})

    beliefs_q = """
    MATCH (t:AgentType {id: $id})-[r:HOLDS_BELIEF]->(b:Belief)
    RETURN b, r.strength as strength
    ORDER BY r.strength DESC
    """
    beliefs = client.query(beliefs_q, {"id": type_id})

    taboos_q = """
    MATCH (t:AgentType {id: $id})-[r:OBSERVES_TABOO]->(tb:Taboo)
    RETURN tb, r.severity as severity
    """
    taboos = client.query(taboos_q, {"id": type_id})

    prompts_q = """
    MATCH (t:AgentType {id: $id})-[:HAS_PROMPT]->(p:Prompt)
    RETURN p
    """
    prompts = client.query(prompts_q, {"id": type_id})

    tools_q = """
    MATCH (t:AgentType {id: $id})-[:HAS_TOOL]->(tool:Tool)
    RETURN tool
    """
    tools = client.query(tools_q, {"id": type_id})

    return {
        **agent_type,
        "virtues": [
            {**dict(row[0].properties), "priority": row[1]}
            for row in virtues if row[0]
        ],
        "kuleanas": [
            {**dict(row[0].properties), "priority": row[1]}
            for row in kuleanas if row[0]
        ],
        "beliefs": [
            {**dict(row[0].properties), "strength": row[1]}
            for row in beliefs if row[0]
        ],
        "taboos": [
            {**dict(row[0].properties), "severity": row[1]}
            for row in taboos if row[0]
        ],
        "prompts": [dict(row[0].properties) for row in prompts if row[0]],
        "tools": [dict(row[0].properties) for row in tools if row[0]],
    }


@app.get("/api/virtues")
def get_virtues():
    """Get all virtues."""
    client = get_client()
    query = "MATCH (v:Virtue) RETURN v ORDER BY v.name"
    result = client.query(query)
    return {
        "virtues": [dict(row[0].properties) for row in result if row[0]]
    }


@app.get("/api/kuleanas")
def get_kuleanas():
    """Get all kuleanas."""
    client = get_client()
    query = "MATCH (k:Kuleana) RETURN k ORDER BY k.name"
    result = client.query(query)
    return {
        "kuleanas": [dict(row[0].properties) for row in result if row[0]]
    }


@app.get("/api/beliefs")
def get_beliefs():
    """Get all beliefs."""
    client = get_client()
    query = "MATCH (b:Belief) RETURN b"
    result = client.query(query)
    return {
        "beliefs": [dict(row[0].properties) for row in result if row[0]]
    }


@app.get("/api/taboos")
def get_taboos():
    """Get all taboos."""
    client = get_client()
    query = "MATCH (t:Taboo) RETURN t"
    result = client.query(query)
    return {
        "taboos": [dict(row[0].properties) for row in result if row[0]]
    }


@app.get("/api/lore")
def get_lore():
    """Get all lore."""
    client = get_client()
    query = "MATCH (l:Lore) RETURN l ORDER BY l.importance DESC"
    result = client.query(query)
    return {
        "lore": [dict(row[0].properties) for row in result if row[0]]
    }


@app.get("/api/voice")
def get_voice():
    """Get all voice patterns."""
    client = get_client()
    query = "MATCH (v:VoicePattern) RETURN v"
    result = client.query(query)
    return {
        "voice_patterns": [dict(row[0].properties) for row in result if row[0]]
    }


# --- Agent Operations ---

class CreateAgentRequest(BaseModel):
    agent_type_id: str
    instance_id: Optional[str] = None


@app.post("/api/agents/create")
def create_agent(request: CreateAgentRequest):
    """Create a new agent instance."""
    try:
        bridge = get_bridge()
        agent = bridge.create_agent(request.agent_type_id, request.instance_id)
        return {
            "success": True,
            "instance_id": agent.instance_id,
            "name": agent.name,
            "type_id": agent.type_id,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/agents/{instance_id}")
def get_agent(instance_id: str):
    """Get agent instance details."""
    try:
        bridge = get_bridge()
        agent = bridge.get_agent(instance_id)
        if not agent:
            return {"error": "Agent not found"}

        return {
            "instance_id": agent.instance_id,
            "name": agent.name,
            "type_id": agent.type_id,
            "virtues": [v["name"] for v in agent.virtues],
            "kuleanas": [k["name"] for k in agent.kuleanas],
            "tools": agent.get_tool_names(),
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/agents/{instance_id}/prompt")
def get_agent_prompt(instance_id: str):
    """Get the full system prompt for an agent."""
    try:
        bridge = get_bridge()
        prompt = bridge.get_agent_prompt(instance_id)
        return {"prompt": prompt}
    except Exception as e:
        return {"error": str(e)}


class CheckActionRequest(BaseModel):
    action: str


@app.post("/api/agents/{instance_id}/check-action")
def check_action(instance_id: str, request: CheckActionRequest):
    """Check if an action is allowed by agent's constraints."""
    try:
        bridge = get_bridge()
        result = bridge.check_action(instance_id, request.action)
        return result
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# HTML UI
# ============================================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Soul Kiln Test UI v2</title>
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
        .badge { background: var(--success); color: black; padding: 2px 8px; border-radius: 3px; font-size: 0.8em; }

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
        nav button {
            display: block;
            width: 100%;
            padding: 10px 15px;
            background: var(--secondary);
            color: var(--text);
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-align: left;
            font-size: 0.95em;
            transition: all 0.2s;
        }
        nav button:hover { background: var(--primary); }
        nav button.active { background: var(--primary); }

        main { background: var(--surface); padding: 20px; border-radius: 8px; min-height: 600px; }

        .section { margin-bottom: 30px; }
        .section h2 { color: var(--primary); margin-bottom: 15px; border-bottom: 1px solid var(--secondary); padding-bottom: 10px; }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
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
        .stat .label { color: var(--text-dim); font-size: 0.8em; }

        .card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; }
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
        .card .meta { margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap; }
        .tag {
            background: var(--secondary);
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.75em;
            color: var(--text-dim);
        }
        .tag.priority { background: var(--primary); color: white; }
        .tag.type { background: #0d9488; }

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
            white-space: pre-wrap;
        }

        .form-group { margin: 15px 0; }
        .form-group label { display: block; margin-bottom: 5px; color: var(--text-dim); }
        .form-group input, .form-group select {
            width: 100%;
            padding: 10px;
            background: var(--bg);
            border: 1px solid var(--secondary);
            border-radius: 5px;
            color: var(--text);
        }
        .btn {
            background: var(--primary);
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .btn:hover { opacity: 0.9; }
        .btn-secondary { background: var(--secondary); }

        .result {
            margin-top: 15px;
            padding: 15px;
            background: var(--bg);
            border-radius: 5px;
            border-left: 3px solid var(--success);
        }
        .result.error { border-left-color: var(--primary); }

        .loading { color: var(--text-dim); font-style: italic; }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>Soul Kiln Test UI <span class="badge">v2 - Graph-Based</span></h1>
            <p>Proxy Agent Architecture Explorer - All data from FalkorDB</p>
        </div>
    </header>

    <div class="container">
        <div class="grid">
            <nav>
                <h3>Graph Data</h3>
                <ul>
                    <li><button onclick="loadSection('overview')" class="active" id="nav-overview">Overview</button></li>
                    <li><button onclick="loadSection('agent-types')" id="nav-agent-types">Agent Types</button></li>
                    <li><button onclick="loadSection('virtues')" id="nav-virtues">Virtues</button></li>
                    <li><button onclick="loadSection('kuleanas')" id="nav-kuleanas">Kuleanas</button></li>
                    <li><button onclick="loadSection('beliefs')" id="nav-beliefs">Beliefs</button></li>
                    <li><button onclick="loadSection('taboos')" id="nav-taboos">Taboos</button></li>
                    <li><button onclick="loadSection('lore')" id="nav-lore">Lore</button></li>
                    <li><button onclick="loadSection('voice')" id="nav-voice">Voice</button></li>
                </ul>
                <h3 style="margin-top: 20px;">Agent Operations</h3>
                <ul>
                    <li><button onclick="loadSection('create-agent')" id="nav-create-agent">Create Agent</button></li>
                    <li><button onclick="loadSection('test-agent')" id="nav-test-agent">Test Agent</button></li>
                </ul>
            </nav>

            <main id="content">
                <p class="loading">Loading...</p>
            </main>
        </div>
    </div>

    <script>
        async function loadSection(section) {
            document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
            document.getElementById('nav-' + section)?.classList.add('active');

            const content = document.getElementById('content');
            content.innerHTML = '<p class="loading">Loading...</p>';

            try {
                if (section === 'overview') await renderOverview();
                else if (section === 'agent-types') await renderAgentTypes();
                else if (section === 'virtues') await renderList('virtues', 'Virtues');
                else if (section === 'kuleanas') await renderList('kuleanas', 'Kuleanas');
                else if (section === 'beliefs') await renderList('beliefs', 'Beliefs');
                else if (section === 'taboos') await renderList('taboos', 'Taboos');
                else if (section === 'lore') await renderList('lore', 'Lore');
                else if (section === 'voice') await renderList('voice', 'Voice Patterns', 'voice_patterns');
                else if (section === 'create-agent') renderCreateAgent();
                else if (section === 'test-agent') renderTestAgent();
            } catch (e) {
                content.innerHTML = `<div class="result error"><p>Error: ${e.message}</p></div>`;
            }
        }

        async function renderOverview() {
            const data = await fetch('/api/overview').then(r => r.json());
            const s = data.subsystems;
            document.getElementById('content').innerHTML = `
                <div class="section">
                    <h2>Graph Overview</h2>
                    <div class="stats">
                        <div class="stat"><div class="number">${s.agent_types}</div><div class="label">Agent Types</div></div>
                        <div class="stat"><div class="number">${s.agent_instances}</div><div class="label">Instances</div></div>
                        <div class="stat"><div class="number">${s.virtues}</div><div class="label">Virtues</div></div>
                        <div class="stat"><div class="number">${s.kuleanas}</div><div class="label">Kuleanas</div></div>
                        <div class="stat"><div class="number">${s.beliefs}</div><div class="label">Beliefs</div></div>
                        <div class="stat"><div class="number">${s.taboos}</div><div class="label">Taboos</div></div>
                        <div class="stat"><div class="number">${s.lore}</div><div class="label">Lore</div></div>
                        <div class="stat"><div class="number">${s.voice_patterns}</div><div class="label">Voice</div></div>
                        <div class="stat"><div class="number">${s.prompts}</div><div class="label">Prompts</div></div>
                        <div class="stat"><div class="number">${s.tools}</div><div class="label">Tools</div></div>
                    </div>
                    <p>Graph Status: <span class="badge">${data.graph_status}</span></p>
                </div>
            `;
        }

        async function renderAgentTypes() {
            const data = await fetch('/api/agent-types').then(r => r.json());
            let html = '<div class="section"><h2>Agent Types</h2><div class="card-grid">';

            for (const t of data.agent_types) {
                html += `<div class="card" onclick="showAgentType('${t.id}')">
                    <h4>${t.name || t.id}</h4>
                    <p>${(t.description || '').slice(0, 100)}...</p>
                    <div class="meta">
                        <span class="tag">v${t.version || '1.0'}</span>
                    </div>
                </div>`;
            }

            html += '</div></div><div id="detail"></div>';
            document.getElementById('content').innerHTML = html;
        }

        async function showAgentType(id) {
            const data = await fetch('/api/agent-types/' + id).then(r => r.json());
            document.getElementById('detail').innerHTML = `
                <div class="detail-panel">
                    <h3>${data.name || data.id}</h3>
                    <p style="margin: 10px 0;">${data.description || ''}</p>
                    <p><strong>Virtues (${data.virtues?.length || 0}):</strong> ${data.virtues?.map(v => v.name).join(', ') || 'None'}</p>
                    <p><strong>Kuleanas (${data.kuleanas?.length || 0}):</strong> ${data.kuleanas?.map(k => k.name).join(', ') || 'None'}</p>
                    <p><strong>Beliefs (${data.beliefs?.length || 0}):</strong> ${data.beliefs?.length || 0} loaded</p>
                    <p><strong>Taboos (${data.taboos?.length || 0}):</strong> ${data.taboos?.map(t => t.name).join(', ') || 'None'}</p>
                    <p><strong>Prompts (${data.prompts?.length || 0}):</strong> ${data.prompts?.map(p => p.name).join(', ') || 'None'}</p>
                    <p><strong>Tools (${data.tools?.length || 0}):</strong> ${data.tools?.map(t => t.name).join(', ') || 'None'}</p>
                </div>
            `;
        }

        async function renderList(endpoint, title, key = null) {
            const data = await fetch('/api/' + endpoint).then(r => r.json());
            const items = data[key || endpoint] || [];
            let html = `<div class="section"><h2>${title} (${items.length})</h2><div class="card-grid">`;

            for (const item of items) {
                const name = item.name || item.title || item.id || 'Unnamed';
                const desc = item.description || item.statement || item.content || '';
                html += `<div class="card">
                    <h4>${name}</h4>
                    <p>${desc.slice(0, 120)}${desc.length > 120 ? '...' : ''}</p>
                    <div class="meta">
                        <span class="tag">${item.id}</span>
                    </div>
                </div>`;
            }

            html += '</div></div>';
            document.getElementById('content').innerHTML = html;
        }

        function renderCreateAgent() {
            document.getElementById('content').innerHTML = `
                <div class="section">
                    <h2>Create Agent Instance</h2>
                    <div class="detail-panel">
                        <div class="form-group">
                            <label>Agent Type ID:</label>
                            <input type="text" id="agent-type" value="ambassador" placeholder="e.g., ambassador" />
                        </div>
                        <div class="form-group">
                            <label>Instance ID (optional):</label>
                            <input type="text" id="instance-id" placeholder="Leave blank for auto-generated" />
                        </div>
                        <button class="btn" onclick="createAgent()">Create Agent</button>
                        <div id="create-result"></div>
                    </div>
                </div>
            `;
        }

        async function createAgent() {
            const typeId = document.getElementById('agent-type').value;
            const instanceId = document.getElementById('instance-id').value || null;

            const res = await fetch('/api/agents/create', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({agent_type_id: typeId, instance_id: instanceId})
            }).then(r => r.json());

            const isError = !res.success;
            document.getElementById('create-result').innerHTML = `
                <div class="result ${isError ? 'error' : ''}">
                    ${isError
                        ? `<p>Error: ${res.error}</p>`
                        : `<p>Created agent: <strong>${res.name}</strong></p>
                           <p>Instance ID: <code>${res.instance_id}</code></p>`
                    }
                </div>
            `;
        }

        function renderTestAgent() {
            document.getElementById('content').innerHTML = `
                <div class="section">
                    <h2>Test Agent</h2>
                    <div class="detail-panel">
                        <div class="form-group">
                            <label>Agent Instance ID:</label>
                            <input type="text" id="test-instance-id" placeholder="Enter instance ID" />
                        </div>
                        <button class="btn" onclick="loadAgentDetails()">Load Agent</button>
                        <div id="agent-details"></div>

                        <hr style="margin: 20px 0; border-color: var(--secondary);" />

                        <h3>Action Check</h3>
                        <div class="form-group">
                            <label>Action to check:</label>
                            <input type="text" id="action-check" placeholder="e.g., recommend a private loan" />
                        </div>
                        <button class="btn btn-secondary" onclick="checkAgentAction()">Check Action</button>
                        <div id="action-result"></div>

                        <hr style="margin: 20px 0; border-color: var(--secondary);" />

                        <h3>View System Prompt</h3>
                        <button class="btn btn-secondary" onclick="viewPrompt()">View Full Prompt</button>
                        <div id="prompt-result"></div>
                    </div>
                </div>
            `;
        }

        async function loadAgentDetails() {
            const instanceId = document.getElementById('test-instance-id').value;
            const res = await fetch('/api/agents/' + instanceId).then(r => r.json());

            if (res.error) {
                document.getElementById('agent-details').innerHTML = `<div class="result error"><p>${res.error}</p></div>`;
                return;
            }

            document.getElementById('agent-details').innerHTML = `
                <div class="result">
                    <p><strong>Name:</strong> ${res.name}</p>
                    <p><strong>Type:</strong> ${res.type_id}</p>
                    <p><strong>Virtues:</strong> ${res.virtues?.join(', ') || 'None'}</p>
                    <p><strong>Kuleanas:</strong> ${res.kuleanas?.join(', ') || 'None'}</p>
                    <p><strong>Tools:</strong> ${res.tools?.join(', ') || 'None'}</p>
                </div>
            `;
        }

        async function checkAgentAction() {
            const instanceId = document.getElementById('test-instance-id').value;
            const action = document.getElementById('action-check').value;

            const res = await fetch('/api/agents/' + instanceId + '/check-action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action})
            }).then(r => r.json());

            const isAllowed = res.allowed;
            document.getElementById('action-result').innerHTML = `
                <div class="result ${isAllowed ? '' : 'error'}">
                    <p><strong>${isAllowed ? '✓ ALLOWED' : '✗ BLOCKED'}</strong></p>
                    ${res.reason ? `<p>Reason: ${res.reason}</p>` : ''}
                    ${res.details ? `<pre>${JSON.stringify(res.details, null, 2)}</pre>` : ''}
                    ${res.virtue_alignment ? `<pre>${JSON.stringify(res.virtue_alignment, null, 2)}</pre>` : ''}
                </div>
            `;
        }

        async function viewPrompt() {
            const instanceId = document.getElementById('test-instance-id').value;
            const res = await fetch('/api/agents/' + instanceId + '/prompt').then(r => r.json());

            if (res.error) {
                document.getElementById('prompt-result').innerHTML = `<div class="result error"><p>${res.error}</p></div>`;
                return;
            }

            document.getElementById('prompt-result').innerHTML = `
                <div class="result">
                    <pre>${res.prompt || 'No prompt available'}</pre>
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
