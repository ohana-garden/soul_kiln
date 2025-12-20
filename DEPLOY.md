# Deploying Soul Kiln to Railway

## Overview

Soul Kiln requires two services:
1. **FalkorDB** - Graph database (Redis-based)
2. **soul-kiln** - FastAPI application

## Quick Deploy

### 1. Create Railway Project

```bash
railway login
railway init
```

### 2. Deploy FalkorDB Service

Railway doesn't have native FalkorDB support, so deploy via Docker:

```bash
# In Railway dashboard:
# 1. Click "New Service"
# 2. Select "Docker Image"
# 3. Enter: falkordb/falkordb:latest
# 4. Set start command: --loadmodule /usr/lib/redis/modules/falkordb.so
# 5. Add TCP proxy on port 6379
```

Or use the provided Dockerfile:

```bash
cd deploy/falkordb
railway up
```

### 3. Deploy Soul Kiln App

```bash
# From project root
railway up
```

### 4. Configure Environment Variables

In Railway dashboard, set these variables for the soul-kiln service:

```
FALKORDB_HOST=${{falkordb.RAILWAY_TCP_PROXY_DOMAIN}}
FALKORDB_PORT=${{falkordb.RAILWAY_TCP_PROXY_PORT}}
FALKORDB_GRAPH=soul_kiln
LOG_LEVEL=INFO
```

Replace `falkordb` with your FalkorDB service name.

## Project Structure

```
railway.toml          # Railway config for soul-kiln app
Dockerfile            # Main app container
deploy/
  falkordb/
    Dockerfile        # FalkorDB container
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FALKORDB_HOST` | FalkorDB hostname | localhost |
| `FALKORDB_PORT` | FalkorDB port | 6379 |
| `FALKORDB_GRAPH` | Graph name | soul_kiln |
| `LOG_LEVEL` | Logging level | INFO |
| `ANTHROPIC_API_KEY` | For LLM features | (optional) |

## Endpoints

Once deployed:

- `GET /` - Service info
- `GET /health` - Health check
- `GET /docs` - OpenAPI documentation
- `GET /api/virtues` - List all 19 virtues
- `GET /api/graph/status` - Graph database status
- `WS /ws/{session_id}` - WebSocket theatre connection

## Local Development

```bash
# Start FalkorDB locally
docker-compose up -d

# Run the app
uvicorn src.main:app --reload --port 8000
```

## Troubleshooting

### FalkorDB Connection Failed

1. Check FALKORDB_HOST and FALKORDB_PORT are set
2. Verify FalkorDB service is running
3. Check Railway service logs

### Health Check Failing

The app can run in "limited mode" without FalkorDB. Check `/api/graph/status` for connection details.

### WebSocket Issues

Ensure Railway TCP proxy is enabled for the FalkorDB service if using external connections.
