# Building and Pushing OpenMemory Images to Docker Hub

This guide explains how to build production-ready Docker images with code baked in and push them to Docker Hub.

## Prerequisites

1. Docker installed and running
2. Docker Hub account (create at https://hub.docker.com)
3. Logged into Docker Hub: `docker login`

## Current Setup Analysis

### Development Setup (Current)
- **Volume mounts**: Code is mounted from host (`./api:/usr/src/openmemory:rw`)
- **Purpose**: Hot-reload during development
- **Problem**: Won't work for Docker Hub - users won't have your source code

### Production Setup (What We're Building)
- **Code baked in**: Dockerfile copies code into image
- **No volume mounts**: Code comes from image, not host
- **Result**: Works anywhere, no source code needed

## Step 1: Build Production Images

### Build MCP API Image

```bash
cd /home/otto_cs_03/pproj/memory/mem0-source/mem0-1.0.0/openmemory

# Build the API image with your Docker Hub username
docker build -t your-dockerhub-username/openmemory-mcp-gemini:latest -f api/Dockerfile api/

# Tag with version (optional but recommended)
docker tag your-dockerhub-username/openmemory-mcp-gemini:latest your-dockerhub-username/openmemory-mcp-gemini:v1.0.0
```

### Build UI Image

```bash
# Build the UI image
docker build -t your-dockerhub-username/openmemory-ui-gemini:latest -f ui/Dockerfile ui/

# Tag with version (optional but recommended)
docker tag your-dockerhub-username/openmemory-ui-gemini:latest your-dockerhub-username/openmemory-ui-gemini:v1.0.0
```

## Step 2: Test Images Locally (Without Volume Mounts)

Create a test docker-compose file to verify images work standalone:

```bash
# Use the production docker-compose.yml (update image names first)
docker compose -f docker-compose.production.yml up -d

# Check logs
docker logs openmemory-mcp
docker logs openmemory-ui

# Test API
curl http://localhost:8765/health

# If everything works, stop and proceed to push
docker compose -f docker-compose.production.yml down
```

## Step 3: Push to Docker Hub

```bash
# Push MCP API image
docker push your-dockerhub-username/openmemory-mcp-gemini:latest
docker push your-dockerhub-username/openmemory-mcp-gemini:v1.0.0

# Push UI image
docker push your-dockerhub-username/openmemory-ui-gemini:latest
docker push your-dockerhub-username/openmemory-ui-gemini:v1.0.0
```

## Step 4: Update docker-compose.production.yml

Edit `docker-compose.production.yml` and replace:
- `your-dockerhub-username` with your actual Docker Hub username

## Step 5: Create Installation Guide

Users can now install with:

```bash
# 1. Set environment variables
export GOOGLE_API_KEY=your-key-here
export NEO4J_PASSWORD=your-secure-password

# 2. Download docker-compose.production.yml
# (You'll provide this file)

# 3. Run
docker compose -f docker-compose.production.yml up -d
```

## Key Differences: Development vs Production

| Aspect | Development (Current) | Production (Docker Hub) |
|--------|----------------------|------------------------|
| Code Location | Host filesystem (volume mount) | Baked into image |
| Volume Mounts | `./api:/usr/src/openmemory:rw` | Only data volumes |
| Hot Reload | Yes (`--reload` flag) | No (production mode) |
| Source Code Required | Yes | No |
| Works Anywhere | Only on your machine | Any Docker host |

## Verification Checklist

- [ ] Images build successfully
- [ ] Images run without volume mounts
- [ ] API responds at `http://localhost:8765/health`
- [ ] UI loads at `http://localhost:3000`
- [ ] MCP server name is `openmemory-local`
- [ ] Images pushed to Docker Hub
- [ ] docker-compose.production.yml updated with correct image names
- [ ] Tested on a clean machine (or different user)

## Troubleshooting

### Image doesn't have code
- Check Dockerfile has `COPY . .` before `CMD`
- Rebuild image: `docker build --no-cache ...`

### Container can't find files
- Verify no volume mounts overriding `/usr/src/openmemory`
- Check working directory in Dockerfile matches CMD

### MCP server not found
- Verify `mcp = FastMCP("openmemory-local")` in code
- Check container logs: `docker logs openmemory-mcp`

