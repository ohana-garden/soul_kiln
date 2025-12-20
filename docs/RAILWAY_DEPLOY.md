# Railway Deployment Guide

Deploy Soul Kiln to Railway with FalkorDB.

## Architecture

Soul Kiln uses graphiti-core as a library to connect directly to FalkorDB:

```
FalkorDB (graph database)
    ↓
Soul-Kiln (uses graphiti-core library)
```

## Prerequisites

- Railway account (https://railway.app)
- GitHub repo connected to Railway
- Anthropic API key

## Quick Deploy (2 Services)

### Step 1: Create Railway Project

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select `ohana-garden/soul_kiln`

### Step 2: Add FalkorDB Service

1. In your Railway project, click **"+ New"**
2. Select **"Docker Image"**
3. Enter: `falkordb/falkordb:latest`
4. Click **"Add"**
5. Go to **Settings** → **Networking**:
   - Add internal port: `6379`
6. Go to **Settings** → **Variables**:
   - Add: `FALKORDB_ARGS=--timeout 0`
7. Go to **Volumes** → **Add Volume**:
   - Mount path: `/data`

### Step 3: Configure Soul-Kiln Service

1. Click on the main service (deployed from root)
2. Go to **Settings** → **Variables**:
   ```
   ANTHROPIC_API_KEY=sk-ant-xxxxx
   FALKORDB_HOST=falkordb.railway.internal
   FALKORDB_PORT=6379
   ```
3. Go to **Settings** → **Networking**:
   - Generate a public domain

## Environment Variables Reference

### Soul-Kiln (Main App)

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude |
| `FALKORDB_HOST` | Auto | FalkorDB hostname (auto: falkordb.railway.internal) |
| `FALKORDB_PORT` | Auto | FalkorDB port (default: 6379) |
| `PORT` | Auto | Railway injects this automatically |

### FalkorDB Service

| Variable | Required | Description |
|----------|----------|-------------|
| `FALKORDB_ARGS` | No | FalkorDB arguments (recommended: `--timeout 0`) |

## Verify Deployment

After all services are running:

1. **Check health endpoint:**
   ```bash
   curl https://your-app.railway.app/health
   ```

2. **Expected response:**
   ```json
   {
     "status": "healthy",
     "components": {
       "graph": {"status": "healthy"},
       "graphiti": {"status": "healthy"},
       "vessels": {"status": "healthy"}
     }
   }
   ```

3. **Check API docs:**
   - Visit: `https://your-app.railway.app/docs`

## Troubleshooting

### Service won't start
- Check logs in Railway dashboard
- Verify all environment variables are set
- Ensure FalkorDB is healthy first

### Health check failing
- FalkorDB may still be initializing
- Check internal networking is configured
- Verify port 6379 is exposed internally

### FalkorDB connection issues
- Confirm `FALKORDB_HOST=falkordb.railway.internal`
- Check FalkorDB service is named exactly `falkordb`
- Ensure internal port 6379 is configured

## Service Dependencies

```
FalkorDB (must start first)
    ↓
Soul-Kiln (uses graphiti-core library to connect to FalkorDB)
```

Railway handles this automatically if services are properly configured.
