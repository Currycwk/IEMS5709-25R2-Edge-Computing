# Docker Compose Introduction

## What is Docker Compose?

Docker Compose is a tool for defining and running multi-container Docker applications. With Compose, you use a YAML file to configure your application’s services. Then, with a single command, you create and start all the services from your configuration.

## Why use Docker Compose?

Docker Compose makes it easy to create and manage multi-container Docker applications. It is a great way to test and deploy your applications in a consistent and reproducible way.

## Example Application

### Manual Start-up

In this section we start the backend and frontend containers **manually** (without Docker Compose) to understand what Docker Compose does for us automatically.

**Step 1 — Build the backend image:**

```bash
cd /proj_data/zst/TA_2026/IEMS5709-25R2-Edge-Computing/Lab3
docker build -f Dockerfile.backend -t calc-backend .
```

**Step 2 — Run the backend container (publish port 6060 to the host):**

```bash
docker run -d -p 6060:6060 --name calc-backend calc-backend
```

**Test the backend API:**

```bash
curl -s -X POST http://localhost:6060/calculate \
  -H "Content-Type: application/json" \
  -d '{"a":1,"b":2,"op":"+"}'  | jq
```


**Step 3 — Build the frontend image:**

```bash
docker build -f Dockerfile.frontend -t calc-frontend .
```

**Step 4 — Run the frontend container:**

```bash
docker run -d -p 5959:5959 --name calc-frontend calc-frontend
```

**Step 5 — Verify:**

- Frontend UI: http://&lt;host-ip&gt;:5959
- Backend API (from remote client): http://&lt;host-ip&gt;:6060

**Step 6 — Tear down (optional):**

```bash
docker stop calc-frontend calc-backend
docker rm   calc-frontend calc-backend
```

> **Why is this cumbersome?** Every time we want to start the app we have to run four commands in the correct order. Docker Compose lets us replace all of the above with a single `docker compose up -d`.

## Compose File Structure

```yaml
# docker-compose.yaml
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: calc-backend
    ports:
      - "6060:6060"
      
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: calc-frontend
    ports:
      - "5959:5959"
    depends_on:
      - backend
```

Line by line explanation:

| Line | Explanation |
|------|-------------|
| `services:` | Top-level key that lists all containers (services) to run |
| `build.context` / `dockerfile` | Build each image from the Lab3 directory using the matching Dockerfile |
| `container_name: calc-backend` | Assigns a fixed name to the container (optional but helpful) |
| `ports: ["6060:6060"]` / `["5959:5959"]` | Publish backend and static server so a **browser on a remote client** can reach them via `http://<host-ip>:5959` and `http://<host-ip>:6060` |
| `depends_on: [backend]` | Starts backend before frontend (ordering only; health checks are a separate topic) |
| Default network | Compose attaches services to one network; service DNS names exist for **container-to-container** traffic (this demo uses `localhost` in JS instead) |

## Start the App with Docker Compose

```bash
docker compose -p "test-app" up -d
```

That's it — one command replaces all four manual steps above. Docker Compose reads `docker-compose.yaml`, builds both images, creates a shared network, and starts both containers in the correct order.


## Common Commands

```bash
# Start the application
docker compose -p "test-app" up -d

# Stop running containers without removing them
docker compose -p "test-app" stop

# Start the stopped containers
docker compose -p "test-app" start

# Restart the application
docker compose -p "test-app" restart

# Show logs
docker compose -p "test-app" logs -f

# Show running containers
docker compose -p "test-app" ps

# Stop the application
docker compose -p "test-app" down

# list all compose projects
docker compose ls
```


## References

https://docs.docker.com/reference/cli/docker/compose/