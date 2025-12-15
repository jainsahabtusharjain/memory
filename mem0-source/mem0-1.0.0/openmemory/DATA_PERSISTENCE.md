# Data Persistence Guide - Docker Hub Deployment

## How Data Persistence Works

When users pull your images from Docker Hub and run them, **data is automatically persisted** using Docker volumes. No manual mounting required!

## Understanding Docker Volumes

### What Gets Stored Where

| Data Type            | Storage Location                         | Volume Name       | Persists?        |
| -------------------- | ---------------------------------------- | ----------------- | ---------------- |
| **SQLite Database**  | `/usr/src/openmemory/data/openmemory.db` | `openmemory_data` | ✅ Yes            |
| **Qdrant Vectors**   | `/qdrant/storage`                        | `qdrant_storage`  | ✅ Yes            |
| **Neo4j Graph Data** | `/data`                                  | `neo4j_data`      | ✅ Yes            |
| **Neo4j Logs**       | `/logs`                                  | `neo4j_logs`      | ✅ Yes            |
| **Application Code** | Baked into image                         | N/A               | ✅ Yes (in image) |

### How It Works

1. **Code is in the image** (baked in during build)
   - No volume mount needed
   - Users don't need source code

2. **Data uses Docker volumes** (automatic)
   - Docker creates volumes automatically
   - Data persists even if containers are removed
   - Data survives `docker compose down` and `docker compose up`

## Example: User's First Run

```bash
# User downloads your docker-compose.production.yml
# Sets environment variables
export GOOGLE_API_KEY=their-key-here

# Runs docker compose
docker compose -f docker-compose.production.yml up -d
```

**What happens:**
1. Docker pulls images from Docker Hub
2. Docker creates volumes automatically:
   - `openmemory_data` (for SQLite)
   - `qdrant_storage` (for vectors)
   - `neo4j_data` (for graph data)
   - `neo4j_logs` (for Neo4j logs)
3. Containers start with data volumes attached
4. Data is stored in Docker-managed volumes

## Where Docker Stores Volumes

Docker stores volumes in:
- **Linux**: `/var/lib/docker/volumes/`
- **Mac/Windows**: Inside Docker Desktop VM

Users can find their volumes:
```bash
# List all volumes
docker volume ls

# Inspect a specific volume
docker volume inspect openmemory_data

# See where data is stored
docker volume inspect openmemory_data | grep Mountpoint
```

## Data Persistence Scenarios

### Scenario 1: Container Restart
```bash
docker compose restart openmemory-mcp
```
✅ **Data persists** - Volumes remain attached

### Scenario 2: Container Removal
```bash
docker compose down
docker compose up -d
```
✅ **Data persists** - Volumes are not removed by default

### Scenario 3: Volume Removal (Data Loss)
```bash
docker compose down -v  # -v removes volumes
```
❌ **Data is lost** - Volumes are deleted

### Scenario 4: Image Update
```bash
docker compose pull  # Pull new images
docker compose up -d  # Restart with new images
```
✅ **Data persists** - Volumes remain, only code updates

## Backup and Restore

### Backup Data
```bash
# Backup SQLite database
docker exec openmemory-mcp cat /usr/src/openmemory/data/openmemory.db > backup.db

# Backup Qdrant data (volume location)
docker volume inspect qdrant_storage
# Copy files from the Mountpoint location

# Backup Neo4j data
docker volume inspect neo4j_data
# Copy files from the Mountpoint location
```

### Restore Data
```bash
# Restore SQLite database
docker cp backup.db openmemory-mcp:/usr/src/openmemory/data/openmemory.db

# Restore volumes (requires stopping containers first)
docker compose down
# Copy files to volume mountpoints
docker compose up -d
```

## Production docker-compose.yml Configuration

Looking at your `docker-compose.production.yml`:

```yaml
volumes:
  # These are Docker-managed volumes
  # Created automatically, persist data
  qdrant_storage:
    driver: local
  openmemory_data:
    driver: local
  neo4j_data:
    driver: local
  neo4j_logs:
    driver: local
```

**Key Points:**
- `driver: local` = Docker manages storage
- No `external: true` = Docker creates them automatically
- No host path specified = Docker chooses location
- Data persists across container restarts

## Alternative: Named Host Paths (Optional)

If users want to control where data is stored, they can modify volumes:

```yaml
volumes:
  openmemory_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /path/to/their/data
```

But the default (Docker-managed) is simpler and works for most users.

## Summary

✅ **Users don't need to:**
- Mount any host directories
- Have source code
- Configure volume paths
- Worry about data location

✅ **Docker automatically:**
- Creates volumes
- Persists data
- Manages storage
- Handles cleanup (only if explicitly requested)

✅ **Data persists:**
- Across container restarts
- Across `docker compose down/up`
- Across image updates
- Until volumes are explicitly removed

## FAQ

**Q: What if a user wants to backup data?**
A: They can use `docker volume inspect` to find the volume location, or use `docker exec` to copy files from containers.

**Q: Can users change where data is stored?**
A: Yes, they can modify `docker-compose.production.yml` to use host paths instead of Docker volumes.

**Q: What happens if a user runs `docker compose down -v`?**
A: All volumes are deleted, and data is lost. This is intentional for cleanup.

**Q: How do users migrate data to a new server?**
A: They can backup volumes (see Backup section above) and restore on the new server.




