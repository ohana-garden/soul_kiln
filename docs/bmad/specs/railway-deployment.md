# Railway Deployment Specification

```yaml
spec:
  id: railway-deployment
  version: 1.0.0
  status: draft
  type: deployment
  dependencies:
    - soul-kiln-codebase
    - virtue-basin-platform

phases:
  - graphiti-integration
  - railway-config
  - standalone-deploy
  - testing
```

---

## Overview

**Goal:** Deploy soul_kiln as a standalone Railway application with full Graphiti integration.

**Stack:**
```
┌─────────────────────────────────────────┐
│           soul_kiln (Python)            │
│         [Railway: GitHub deploy]        │
└───────────────────┬─────────────────────┘
                    │
┌───────────────────▼─────────────────────┐
│         Graphiti (FastAPI Server)       │
│         [Railway: Docker deploy]        │
└───────────────────┬─────────────────────┘
                    │
┌───────────────────▼─────────────────────┐
│              FalkorDB                   │
│         [Railway: Docker image]         │
└─────────────────────────────────────────┘
```

**Outcome:** One-click Railway deploy from GitHub with all services connected.

---

## Phase 1: Graphiti Integration

### 1.1 Current State

| Component | Status | Location |
|-----------|--------|----------|
| `graphiti-core>=0.5.0` | In pyproject.toml | ✅ Dependency exists |
| `SemanticMemory` | Placeholder stub | `src/vessels/memory/semantic.py` |
| `SharedMemory` | Uses FalkorDB directly | `src/agents/memory.py` |
| Graphiti server | Missing | ❌ Not in docker-compose |

### 1.2 Required Changes

#### `src/vessels/memory/graphiti_memory.py` (NEW)
**Replace stub with real Graphiti client.**

```python
class GraphitiMemory:
    """
    Graphiti-backed semantic memory using FalkorDB.

    Provides:
    - Temporal knowledge graph storage
    - Episodic memory with timestamps
    - Semantic search via embeddings
    - Entity and relationship extraction
    """

    def __init__(self, falkordb_host, falkordb_port):
        # Connect Graphiti to FalkorDB

    def add_episode(self, content, agent_id, metadata):
        # Store episodic memory

    def search(self, query, limit, filters):
        # Semantic search

    def get_entity_graph(self, entity_id):
        # Retrieve knowledge subgraph
```

| Function | Purpose |
|----------|---------|
| `add_episode()` | Store temporal episode |
| `search()` | Semantic query |
| `get_entity_graph()` | Knowledge retrieval |
| `build_context()` | Assemble agent context |

#### `src/agents/memory.py` (UPDATE)
**Wire SharedMemory to Graphiti.**

```python
# Current: SharedMemory uses FalkorDB substrate directly
# Change: Add Graphiti layer for semantic operations

class SharedMemory:
    def __init__(self, substrate, edge_manager, node_manager, graphiti_client):
        self.graphiti = graphiti_client  # ADD

    def remember_episode(self, agent_id, content, virtue_context):
        # Store in Graphiti with virtue metadata

    def recall_relevant(self, query, agent_id):
        # Semantic search through Graphiti
```

#### `src/vessels/integration.py` (UPDATE)
**Replace SemanticMemory with GraphitiMemory.**

```python
# Current
from src.vessels.memory.semantic import SemanticMemory
self.semantic_memory = SemanticMemory(max_memories=max_memories)

# Change to
from src.vessels.memory.graphiti_memory import GraphitiMemory
self.graphiti_memory = GraphitiMemory(
    host=os.getenv("FALKORDB_HOST", "localhost"),
    port=os.getenv("FALKORDB_PORT", 6379),
)
```

### 1.3 Graphiti Server

#### `docker/graphiti/Dockerfile` (NEW)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install graphiti-core fastapi uvicorn

# Graphiti server entrypoint
COPY graphiti_server.py .

CMD ["uvicorn", "graphiti_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### `docker/graphiti/graphiti_server.py` (NEW)

```python
"""
Graphiti API server connecting to FalkorDB.
"""
from fastapi import FastAPI
from graphiti_core import Graphiti

app = FastAPI()

graphiti = Graphiti(
    uri=os.getenv("FALKORDB_URI", "redis://falkordb:6379"),
)

@app.post("/episodes")
async def add_episode(content: str, metadata: dict):
    # Add to knowledge graph

@app.get("/search")
async def search(query: str, limit: int = 10):
    # Semantic search
```

---

## Phase 2: Railway Configuration

### 2.1 Service Configuration Files

#### `railway.toml` (root - soul_kiln app)

```toml
[build]
builder = "RAILPACK"
buildCommand = "pip install -e ."

[deploy]
startCommand = "python -m src.main serve"
healthcheckPath = "/health"
healthcheckTimeout = 300

[service]
name = "soul-kiln"
```

#### `docker/graphiti/railway.toml` (Graphiti service)

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
startCommand = "uvicorn graphiti_server:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"

[service]
name = "graphiti"
```

### 2.2 Environment Variables

| Variable | Service | Purpose |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | soul-kiln | Claude LLM access |
| `FALKORDB_HOST` | soul-kiln, graphiti | Database host |
| `FALKORDB_PORT` | soul-kiln, graphiti | Database port (6379) |
| `GRAPHITI_URL` | soul-kiln | Graphiti API endpoint |
| `FALKORDB_URI` | graphiti | Redis-style connection string |

### 2.3 Docker Compose Update

#### `docker-compose.yml` (UPDATE)

```yaml
version: '3.8'

services:
  falkordb:
    image: falkordb/falkordb:latest
    ports:
      - "6379:6379"
    volumes:
      - falkordb_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  graphiti:
    build:
      context: ./docker/graphiti
    ports:
      - "8000:8000"
    environment:
      - FALKORDB_URI=redis://falkordb:6379
    depends_on:
      falkordb:
        condition: service_healthy

  soul-kiln:
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8080:8080"
    environment:
      - FALKORDB_HOST=falkordb
      - FALKORDB_PORT=6379
      - GRAPHITI_URL=http://graphiti:8000
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - graphiti
      - falkordb

volumes:
  falkordb_data:
```

---

## Phase 3: Standalone Deploy

### 3.1 Pre-Deploy Checklist

| Task | Status |
|------|--------|
| Graphiti integration code complete | ⬜ |
| Graphiti server Dockerfile working locally | ⬜ |
| Updated docker-compose runs locally | ⬜ |
| All tests pass | ⬜ |
| Railway config files in place | ⬜ |
| Environment variables documented | ⬜ |
| Health endpoints implemented | ⬜ |

### 3.2 Railway Deploy Steps

1. **Push to GitHub** (public repo)
2. **Create Railway project**
3. **Add FalkorDB service**
   - New service → Docker image → `falkordb/falkordb:latest`
   - Add volume for persistence
4. **Add Graphiti service**
   - New service → GitHub repo → select `docker/graphiti` path
   - Set `FALKORDB_URI` variable
5. **Add soul-kiln service**
   - New service → GitHub repo → root path
   - Set environment variables
6. **Configure networking**
   - Internal networking between services
   - Public domain for soul-kiln only

### 3.3 Health Endpoints

#### `src/api/health.py` (NEW)

```python
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "falkordb": check_falkordb(),
        "graphiti": check_graphiti(),
    }
```

---

## Phase 4: Testing

### 4.1 Local Testing

```bash
# Build and run all services
docker-compose up --build

# Run test suite
pytest tests/

# Test Graphiti integration
pytest tests/test_graphiti_memory.py

# Test health endpoints
curl http://localhost:8080/health
```

### 4.2 Integration Tests

| Test | Purpose |
|------|---------|
| `test_graphiti_connection` | Graphiti connects to FalkorDB |
| `test_episode_storage` | Episodes persist correctly |
| `test_semantic_search` | Search returns relevant results |
| `test_agent_memory_flow` | Agent → Graphiti → FalkorDB flow |
| `test_health_endpoints` | All services report healthy |

### 4.3 Railway Testing

| Test | Purpose |
|------|---------|
| Service health checks pass | All services running |
| Inter-service communication | Internal networking works |
| Persistence across restarts | FalkorDB volume persists |
| Environment variable injection | Secrets properly loaded |

---

## File Summary

### New Files

| File | Purpose |
|------|---------|
| `src/vessels/memory/graphiti_memory.py` | Graphiti client wrapper |
| `docker/graphiti/Dockerfile` | Graphiti server container |
| `docker/graphiti/graphiti_server.py` | Graphiti FastAPI server |
| `docker/graphiti/railway.toml` | Railway config for Graphiti |
| `railway.toml` | Railway config for soul-kiln |
| `src/api/health.py` | Health check endpoints |
| `tests/test_graphiti_memory.py` | Integration tests |

### Modified Files

| File | Changes |
|------|---------|
| `src/agents/memory.py` | Add Graphiti client |
| `src/vessels/integration.py` | Replace SemanticMemory |
| `docker-compose.yml` | Add graphiti service |
| `docker/Dockerfile` | Update for Railway |
| `config.yml` | Add Graphiti config section |

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Graphiti-FalkorDB compatibility | Test locally first with explicit version pins |
| Railway networking issues | Use Railway's internal DNS (`graphiti.railway.internal`) |
| Cold start latency | Implement connection pooling, warmup endpoint |
| Data loss on redeploy | Ensure FalkorDB volume is persistent |

---

## Success Criteria

1. **Local:** `docker-compose up` runs all three services
2. **Tests:** All integration tests pass
3. **Railway:** One-click deploy works from GitHub
4. **Health:** All health endpoints return healthy
5. **Memory:** Agents can store and retrieve memories via Graphiti

---

*Specification Version: 1.0.0*
*BMAD Method Compatible*
