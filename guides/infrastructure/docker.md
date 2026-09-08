# Docker Style Guide

> [Doctrine](../../README.md) > [Infrastructure](README.md) > Docker

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Targets Docker Engine 27.5+ and Docker Compose v5.0+.

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| Build image | docker build | `docker build -t myapp:1.0 .` |
| Run container | docker run | `docker run -d --name myapp myapp:1.0` |
| Compose up | docker compose | `docker compose up -d` |
| Compose down | docker compose | `docker compose down` |
| Image scan | Trivy | `trivy image myapp:1.0` |
| Format Dockerfile | Hadolint | `hadolint Dockerfile` |
| Compose validate | docker compose | `docker compose config --quiet` |

## Docker Compose File Organization

Projects **MUST** organize Compose files using the `include` directive for modularity.

**Why**: The `include` directive (introduced in Compose 2.20) enables modular,
reusable configurations. It manages relative path resolution correctly and
allows teams to work on separate service configurations simultaneously. This
approach scales better than monolithic `docker-compose.yml` files as
applications grow.

### File Structure

```text
project/
├── compose.yml                    # Main entry point
├── compose.override.yml           # Local development overrides
├── compose.production.yml         # Production configuration
├── compose.database.yml           # Database services (included)
├── compose.cache.yml              # Cache layer (included)
├── compose.monitoring.yml         # Observability stack (included)
├── .dockerignore                  # Keeps secrets out of every build context
├── .gitignore                     # Keeps secrets out of version control
├── .env                           # Non-secret defaults only
├── .env.production                # Non-secret production values only
└── secrets/                       # Development fixtures only; ignored by
    ├── db_password                # Git and Docker, mode 0400
    └── api_key
```

Projects **MUST** keep secret material out of both version control and every
build context, and **MUST** read production secrets from a path outside the
context (for example `/etc/myapp/secrets/`) that deployment tooling
materialises from a secret manager.

**Why**: A `secrets/` directory inside the project root is inside the default
build context, so `COPY . .` copies it into an image layer unless
`.dockerignore` excludes it. Anything committed to Git additionally survives in
history after deletion. The [.dockerignore](#dockerignore) section gives the
exclusion list, and [Secrets vs Environment Variables](#secrets-vs-environment-variables)
covers how the files are consumed at runtime.

### Per-Service Subdirectories

Projects with multiple services **SHOULD** namespace configuration files under
service subdirectories.

**Why**: Multiple services often need similar file names (`config.yaml`,
`settings.json`). Flat structures create conflicts. Per-service subdirectories
provide clear namespacing, enable service-specific data directories, and keep
compose files readable.

```text
stacks/platform/
├── compose.yml              # Service definitions
├── images.yml               # Pinned digests per architecture (optional)
├── traefik/
│   ├── traefik.yml          # Static config
│   ├── config/              # Dynamic config
│   │   └── security.yml
│   └── data/                # Persistent data (if using bind mounts)
├── alloy/
│   └── config.alloy
└── prometheus/
    ├── prometheus.yml
    └── rules/
        └── alerts.yml
```

**Service Directory Pattern**:

| Subdirectory | Purpose | Mount Type |
| ------------ | ------- | ---------- |
| `{service}/config/` | Configuration files | `:ro` bind mount |
| `{service}/data/` | Persistent state | Read-write bind mount |
| `{service}/secrets/` | Service-specific secrets | `:ro` bind mount, excluded from build contexts |

**Volume Mounting**:

```yaml
services:
  traefik:
    volumes:
      - ./traefik/traefik.yml:/etc/traefik/traefik.yml:ro
      - ./traefik/config:/etc/traefik/dynamic:ro
      - traefik-certs:/letsencrypt  # Docker volume for certs
```

### Volume Strategy

Projects **SHOULD** choose volume types based on access patterns.

| Volume Type | Example | Use Case |
| ----------- | ------- | -------- |
| Docker Volume | `traefik-certs:/letsencrypt` | Infrastructure state |
| Bind Mount | `./service/data:/app/data` | Data snapshots with stack |
| External Path | `${MEDIA_PATH}:/media:ro` | Large storage on separate pools |

**Guidelines**:

- Use Docker volumes for single-instance infrastructure services
- Use bind mounts when data should be visible alongside compose files
- Use environment variable paths for large external storage (photos, video)
- With ZFS storage driver, Docker volumes are on ZFS automatically

### Main Compose File with Include

```yaml
# compose.yml
# Main entry point that includes modular sub-stacks

include:
  - compose.database.yml
  - compose.cache.yml
  - compose.monitoring.yml    # Optional: comment out to disable

networks:
  app:
    external: true
  internal:
    internal: true
```

### Include with Override and Environment

Projects **MAY** use the long syntax for environment-specific includes.

```yaml
include:
  - path: compose.database.yml
    env_file: .env.database
    project_directory: ./services/database
```

**Why**: The long syntax provides fine-grained control over project
directories and environment files, enabling complex multi-environment
configurations while maintaining modularity.

## YAML Anchors and Fragments

Projects **MUST** use YAML anchors (`x-` extensions) to reduce duplication.

**Why**: YAML anchors create reusable configuration fragments that ensure
consistency across services and reduce maintenance burden. The `x-` prefix
marks them as extension fields that Compose ignores during validation.

### Service Defaults Fragment

```yaml
# Fragments (top-level, before services)
x-service-defaults: &service-defaults
  restart: unless-stopped
  init: true
  security_opt:
    - no-new-privileges:true
  cap_drop:
    - ALL

services:
  api:
    <<: *service-defaults
    image: myapp/api@sha256:abc123...
    cap_add:
      - NET_BIND_SERVICE  # Add back only required capabilities
```

### Health Check Fragments

```yaml
x-healthcheck-fast: &healthcheck-fast
  interval: 10s
  timeout: 5s
  retries: 3
  start_interval: 2s

x-healthcheck-standard: &healthcheck-standard
  interval: 30s
  timeout: 10s
  retries: 3
  start_interval: 2s
  start_period: 30s

services:
  web:
    healthcheck:
      <<: *healthcheck-fast
      test: ["CMD", "curl", "-f", "http://localhost/health"]
```

**Why**: The `start_interval` parameter (Compose 2.23+) enables faster health
checks during container startup, improving startup time while using longer
intervals for steady-state monitoring.

### Logging Fragments

```yaml
x-logging-standard: &logging-standard
  driver: json-file
  options:
    max-size: "50m"
    max-file: "5"

x-logging-high-volume: &logging-high-volume
  driver: json-file
  options:
    max-size: "100m"
    max-file: "10"

services:
  api:
    logging:
      <<: *logging-standard

  proxy:
    logging:
      <<: *logging-high-volume
```

### Resource Limits Fragment

```yaml
x-ulimits-high: &ulimits-high
  nofile:
    soft: 65536
    hard: 65536

services:
  database:
    ulimits:
      <<: *ulimits-high
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
          pids: 200
        reservations:
          memory: 1G
```

## Security Hardening

### Image Digest Pinning

Projects **MUST** pin images by SHA256 digest, not tags.

**Why**: Tags are mutable and can point to different images over time. Digest
pinning guarantees the exact same image is used for every deployment,
preventing supply chain attacks and ensuring reproducibility. Even if a
registry is compromised, digest-pinned images remain safe.

```yaml
# WRONG: Tags are mutable
services:
  api:
    image: nginx:latest

# CORRECT: SHA256 digest pinning
services:
  api:
    # nginx:1.25.3, pinned 2024-11
    image: nginx@sha256:4c0fdaa8b6341bfdeca5f18f7837462c80cff90527ee35ef185571e1c327beac
```

**Finding Digests**:

```bash
# Get digest for a specific tag
docker pull nginx:1.25.3
docker inspect nginx:1.25.3 --format='{{.RepoDigests}}'

# Or use crane (faster, no download)
crane digest nginx:1.25.3
```

### Multi-Architecture Image Pinning

Projects deploying to multiple architectures **SHOULD** maintain per-architecture
digests.

**Why**: Multi-arch images have different SHA256 digests per platform. Pinning
a single digest fails on other architectures with "exec format error".
Maintaining per-architecture digests ensures reproducible deployments across
ARM64 and AMD64 hosts.

**images.yml Pattern**:

```yaml
# stacks/platform/images.yml
images:
  traefik:
    version: "3.6.5"
    pinned_at: "2025-12-24T22:00:00Z"
    digests:
      amd64: "sha256:d944e3693bbf5a..."
      arm64: "sha256:088e42947073..."
```

**Compose Integration**:

```yaml
# compose.yml - use environment variable for digest
services:
  traefik:
    image: ${TRAEFIK_IMAGE:-traefik:v3.6}

# .env (templated by deployment tooling)
TRAEFIK_IMAGE=traefik@sha256:d944e3693bbf5a...
```

**Finding Per-Architecture Digests**:

```bash
# Get manifest for all platforms
docker manifest inspect traefik:v3.6.5

# Get specific platform digest
docker manifest inspect traefik:v3.6.5 | \
  jq -r '.manifests[] | select(.platform.architecture=="amd64") | .digest'
```

### Security Options

Projects **MUST** use `no-new-privileges:true` to prevent privilege escalation.

**Why**: The `no-new-privileges` flag prevents containers from gaining
additional privileges via setuid/setgid binaries. This blocks a common
container escape vector where attackers exploit setuid binaries to escalate
privileges.

```yaml
services:
  app:
    security_opt:
      - no-new-privileges:true
```

### Capability Dropping

Projects **MUST** drop all capabilities and **MUST** add back only required capabilities.

**Why**: Linux capabilities allow fine-grained privilege control. Dropping all
capabilities (`CAP_DROP: [ALL]`) creates a minimal privilege baseline.
Selectively adding required capabilities (like `NET_BIND_SERVICE` for ports
<1024) follows the principle of least privilege.

```yaml
services:
  app:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Required to bind to port 80/443
```

**Common Required Capabilities**:

- `NET_BIND_SERVICE`: Bind to privileged ports (<1024)
- `CHOWN`: Change file ownership
- `DAC_OVERRIDE`: Bypass file permission checks
- `SETUID`/`SETGID`: Change user/group IDs (use sparingly)

Projects **MUST NOT** use `privileged: true` except for specialized
infrastructure containers (e.g., cAdvisor, node-exporter).

### Read-Only Root Filesystem

Projects **SHOULD** use `read_only: true` with `tmpfs` for temporary directories.

**Why**: A read-only root filesystem prevents attackers from modifying
container binaries or persisting malware. Combining this with tmpfs for `/tmp`
allows ephemeral writes while maintaining immutability.

```yaml
services:
  app:
    read_only: true
    tmpfs:
      - /tmp
      - /var/run
```

### Non-Root Users

Projects **MUST** run containers as non-root users.

**Why**: Running as root increases the attack surface. If an attacker escapes
the container, they have root privileges. Non-root users limit damage even if
the container is compromised.

```yaml
services:
  app:
    user: "1000:1000"
    # Or by name (if user exists in image)
    # user: "nobody:nobody"
```

**Dockerfile Configuration**:

```dockerfile
# Create non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

USER appuser
```

### Resource Limits

Projects **MUST** define memory, CPU, and PID limits.

**Why**: Resource limits prevent denial-of-service attacks and noisy neighbor
problems. Without limits, a compromised or buggy container can exhaust host
resources, affecting other containers.

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
          pids: 100      # Prevent fork bombs
        reservations:
          memory: 128M
```

### Secrets vs Environment Variables

Projects **MUST** deliver sensitive data as secret files, not environment
variables.

**Why**: Environment variables are visible in `docker inspect`, are inherited
by every child process, and are routinely captured in crash dumps and debug
logs. A secret file is mounted at `/run/secrets/<name>`, is readable only by
the services granted it, and is subject to ordinary filesystem permissions.

```yaml
# WRONG: Secrets in environment variables
services:
  app:
    environment:
      - DB_PASSWORD=supersecret  # Visible in docker inspect!

# CORRECT: Secret file, referenced by path
secrets:
  db_password:
    # Development fixture; production reads a path outside the build context
    file: ./secrets/db_password

services:
  app:
    secrets:
      - db_password
    environment:
      - DB_PASSWORD_FILE=/run/secrets/db_password
```

`DB_PASSWORD_FILE` above is application configuration, not a Docker feature.
The `_FILE` suffix is a convention implemented by some images (including the
`mysql` and `postgres` Docker Official Images); every other image needs
application code that reads the file.

**Application Code**:

```python
# Read secret from file
def get_db_password():
    secret_file = os.getenv("DB_PASSWORD_FILE", "/run/secrets/db_password")
    with open(secret_file) as f:
        return f.read().strip()
```

#### Compose Secrets Are Host Files, Not Encrypted Storage

Compose secrets declared with `file:` are **NOT** encrypted and are **NOT**
held in memory. Compose bind-mounts the named host file into the container;
`docker inspect` reports it as a bind mount whose source is the host path, and
the plaintext stays on the host disk for as long as that file exists.

Projects **MUST NOT** treat a Compose secret as protected storage. Projects
**MUST** protect the source file (mode `0400`, owned by the account that runs
the stack, on a directory excluded from Git and from every build context) or
materialise it at deploy time from an external secret manager such as SOPS,
Vault, or a cloud secrets service, and remove it when the stack stops.

Compose secrets work with Linux containers only: Compose delivers each secret
as a single-file bind mount, and Windows containers can bind-mount directories
only.

```bash
# Verify what a Compose secret actually is
docker inspect myapp-app-1 --format '{{json .Mounts}}' | jq '.[] | {Type, Source}'
# {"Type": "bind", "Source": "/etc/myapp/secrets/db_password"}

# Materialise it outside the build context, readable only by the deploy account
umask 077
mkdir -p /etc/myapp/secrets
vault kv get -field=password secret/myapp/db > /etc/myapp/secrets/db_password
chown deploy:deploy /etc/myapp/secrets/db_password
chmod 0400 /etc/myapp/secrets/db_password
```

#### Swarm Secrets

Only Swarm services get encrypted-at-rest secret storage. Projects that need
that guarantee **MUST** deploy to Swarm (`docker stack deploy`) or another
orchestrator with a secret store; standalone containers and plain
`docker compose up` cannot use it.

**Why**: A Swarm secret is sent to the manager over mutual TLS and stored in
the encrypted Raft log. When a task starts, the decrypted secret is mounted
into an in-memory filesystem, and it is unmounted and flushed from the node's
memory when the task stops. On Windows containers, secrets are instead
persisted in clear text on the container's root disk (removed when the
container stops), so BitLocker on the volume holding the Docker root directory
is **REQUIRED** for encryption at rest there.

```bash
# Create the secret in the swarm, not on a shared filesystem
printf '%s' "$DB_PASSWORD" | docker secret create db_password -
```

```yaml
# compose.production.yml, deployed with: docker stack deploy -c ... myapp
secrets:
  db_password:
    external: true  # Managed by the swarm, not read from a host file

services:
  app:
    secrets:
      - db_password
    environment:
      - DB_PASSWORD_FILE=/run/secrets/db_password
```

## Health Checks

Projects **MUST** define health checks for all services.

**Why**: A health check is the only machine-readable statement of whether a
service can serve traffic. Compose gates `depends_on` on it, orchestrators use
it to decide where to route traffic, and operators read it from `docker ps`.

Health checks **MUST NOT** be relied on for recovery. A failing check sets the
container's health status to `unhealthy` and nothing else: the process keeps
running, and Docker Engine restart policies act on container *exit*, not on
health status. A container that is hung but alive stays up indefinitely under
`restart: unless-stopped`.

Projects therefore **MUST** obtain recovery from one of:

- **The application**: retry with exponential back-off and jitter on
  dependency failures, and exit non-zero on unrecoverable state so the restart
  policy applies.
- **An orchestrator**: Kubernetes restarts a container that fails its liveness
  probe more times than the configured tolerance. Compose and Docker Engine
  provide no equivalent.
- **An explicit controller**: a supervisor that consumes
  `docker events --filter event=health_status` and acts on it.

```bash
# An unhealthy container is not restarted: the restart count stays at 0
docker inspect api \
  --format '{{.State.Health.Status}} {{.State.Running}} {{.RestartCount}}'
# unhealthy true 0
```

### HTTP Health Check

```yaml
services:
  api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
      start_interval: 2s
```

**Parameters**:

- `interval`: Time between health checks (steady state)
- `timeout`: Maximum time to wait for check to complete
- `retries`: Number of consecutive failures before marking unhealthy
- `start_period`: Grace period before first check (Compose 2.20+)
- `start_interval`: Fast interval during startup (Compose 2.23+)

### TCP Health Check

```yaml
services:
  database:
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
```

### Exec Health Check

```yaml
services:
  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 3
```

### wget vs curl

Projects **SHOULD** prefer `wget` for health checks in Alpine-based images.

**Why**: `wget` is included in busybox (Alpine base), while `curl` requires
installation. Using `wget` reduces image size and dependency count.

```yaml
# Alpine/busybox (wget included)
test: ["CMD", "wget", "-q", "--spider", "http://localhost:8080/health"]

# Debian/Ubuntu (curl often pre-installed)
test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
```

### Custom Health Check Scripts

Projects **MAY** use custom scripts for complex health checks.

```yaml
services:
  app:
    healthcheck:
      test: ["CMD", "/app/healthcheck.sh"]
      interval: 30s
```

**Example Script**:

```bash
#!/bin/sh
# healthcheck.sh

# Check HTTP endpoint
wget -q --spider http://localhost:8080/health || exit 1

# Check database connectivity
psql -U user -d db -c "SELECT 1" > /dev/null 2>&1 || exit 1

# Check disk space
[ $(df -h / | tail -1 | awk '{print $5}' | sed 's/%//') -lt 90 ] || exit 1

exit 0
```

## Networking

### External Networks

Projects **SHOULD** use external networks for cross-stack communication.

**Why**: External networks enable service discovery across multiple Compose
stacks. This allows modular deployments where monitoring, databases, and
applications are managed independently but can communicate.

```yaml
# Stack 1: Create network
networks:
  traefik:
    driver: bridge

# Stack 2: Reference external network
networks:
  traefik:
    external: true

services:
  app:
    networks:
      - traefik
```

**Creating External Networks**:

```bash
docker network create traefik
docker network create --internal backend
```

### Internal Networks

Projects **MUST** use internal networks for backend services.

**Why**: Internal networks have no external connectivity, preventing backend
services from initiating outbound connections. This limits the blast radius if
a backend service is compromised.

```yaml
networks:
  frontend:
    # External connectivity allowed
  backend:
    internal: true  # No external access

services:
  web:
    networks:
      - frontend
      - backend

  database:
    networks:
      - backend  # Cannot reach internet
```

### Port Binding

Projects **SHOULD** bind ports to specific IPs for security.

**Why**: Binding to `0.0.0.0` exposes services to all network interfaces. Binding
to specific IPs (like Tailscale) restricts access to trusted networks only.

```yaml
services:
  database:
    # WRONG: Exposed to all interfaces
    ports:
      - "5432:5432"

    # CORRECT: Bind to localhost only
    ports:
      - "127.0.0.1:5432:5432"

    # BEST: Bind to Tailscale IP (VPN-only access)
    ports:
      - "${TAILSCALE_IP:-127.0.0.1}:5432:5432"
```

### Network Isolation Example

```yaml
networks:
  public:
    driver: bridge
  private:
    internal: true

services:
  proxy:
    networks:
      - public
    ports:
      - "443:443"

  api:
    networks:
      - public
      - private

  database:
    networks:
      - private  # Not directly accessible
```

## Logging

Projects **MUST** configure log rotation to prevent disk exhaustion.

**Why**: Docker logs are unbounded by default and can fill disk space, causing
system failures. Configuring max size and file count prevents this.

### JSON File Driver

```yaml
x-logging-standard: &logging-standard
  driver: json-file
  options:
    max-size: "50m"    # Rotate after 50 MB
    max-file: "5"      # Keep 5 rotated files (250 MB total)

x-logging-high-volume: &logging-high-volume
  driver: json-file
  options:
    max-size: "100m"   # Larger logs for high-traffic services
    max-file: "10"     # 1 GB total

services:
  api:
    logging:
      <<: *logging-standard

  proxy:
    logging:
      <<: *logging-high-volume
```

### Structured Logging

Projects **SHOULD** use structured JSON logging.

**Why**: Structured logs are easier to parse, search, and analyze. They enable
powerful log aggregation and filtering in tools like Loki, Elasticsearch, or
CloudWatch.

```yaml
services:
  app:
    environment:
      - LOG_FORMAT=json
```

**Application Code (Python)**:

```python
import structlog

logger = structlog.get_logger()
logger.info("user.login", user_id=123, ip="192.168.1.1")
# Output: {"event": "user.login", "user_id": 123, "ip": "192.168.1.1"}
```

### Log Labels

Projects **SHOULD** add labels for log collection tools.

```yaml
services:
  app:
    labels:
      - "logging=promtail"
      - "log_level=info"
```

## Dockerfile Best Practices

### Multi-Stage Builds

Projects **MUST** use multi-stage builds to minimize image size.

**Why**: Multi-stage builds separate build dependencies from runtime
dependencies, reducing image size by 10-100x. Smaller images have fewer
vulnerabilities, faster pull times, and lower storage costs.

```dockerfile
# Stage 1: Build
FROM golang:1.22 AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .  # Requires a .dockerignore that excludes secrets and credentials
RUN CGO_ENABLED=0 go build -o /app/server

# Stage 2: Runtime
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /app/server /server
EXPOSE 8080
ENTRYPOINT ["/server"]
```

### Base Image Selection

Projects **SHOULD** use minimal base images.

**Why**: Smaller base images reduce attack surface, vulnerabilities, and image
size. Distroless images contain only the application and runtime dependencies,
eliminating shell and package managers.

**Image Size Comparison**:

- `ubuntu:22.04`: ~77 MB
- `alpine:3.19`: ~7 MB
- `distroless/static`: ~2 MB
- `scratch`: ~0 MB (static binaries only)

**Choosing Base Images**:

```dockerfile
# Go, Rust (static binaries)
FROM scratch
COPY app /app
ENTRYPOINT ["/app"]

# Go, Rust (with CA certs, timezone data)
FROM gcr.io/distroless/static-debian12:nonroot

# Python, Node.js, Ruby
FROM gcr.io/distroless/python3-debian12:nonroot
FROM gcr.io/distroless/nodejs20-debian12:nonroot

# Alpine (when distroless unavailable)
FROM alpine:3.19
RUN apk add --no-cache ca-certificates
```

### Layer Optimization

Projects **MUST** order Dockerfile instructions from least to most frequently
changed.

**Why**: Docker caches layers. Placing stable instructions early maximizes cache
hits and speeds up builds. Installing dependencies before copying source code
prevents re-downloading packages on every code change.

```dockerfile
# WRONG: Invalidates cache on every code change
FROM python:3.12-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

# CORRECT: Dependencies cached separately
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

A single-stage build ships the whole build context, so every file that
`.dockerignore` fails to exclude is readable in the published image. Multi-stage
builds narrow that to the intermediate stage, which is still cached and
pushable, so the exclusions matter in both cases.

### Combining RUN Commands

Projects **SHOULD** combine RUN commands to reduce layers.

```dockerfile
# WRONG: Multiple layers
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get clean

# CORRECT: Single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

### .dockerignore

Projects **MUST** use `.dockerignore` to exclude unnecessary files, and
**MUST** exclude every path that can hold credentials.

**Why**: `.dockerignore` reduces build context size and speeds up builds, but
it is also the only thing standing between `COPY . .` and a credential baked
into a layer. Patterns are matched against the whole path relative to the
context root, and `*` does not cross `/`, so `secrets/` and `*.pem` exclude
only top-level matches: `sub/secrets/db_password` and `sub/deploy.pem` still
enter the context. Credential patterns therefore need a `**/` prefix.

```text
# .dockerignore
# Credentials and secret material (never in a build context)
**/secrets/
**/.env*
**/*.pem
**/*.key
**/*.p12
**/*.pfx
**/id_rsa*
**/id_ed25519*
**/.ssh/
**/.aws/
**/.netrc
**/.npmrc
**/.pypirc
**/*.kubeconfig

# Version control and CI metadata
.git
.gitignore
.github

# Build output and caches
node_modules
__pycache__
*.pyc
.pytest_cache
coverage
dist
build

# Documentation and logs
*.md
*.log
```

The matching `.gitignore` **MUST** cover the same credential paths, because a
file removed from the working tree survives in Git history. Git applies these
patterns at every depth, so it needs no `**/` prefix.

```text
# .gitignore
secrets/
.env
.env.*
!.env.example
*.pem
*.key
```

### Build-Time Credentials

Projects **MUST** pass build-time credentials with BuildKit secret or SSH
mounts, and **MUST NOT** pass them as build arguments, environment variables,
or copied files.

**Why**: A build argument persists in the image configuration and in
`docker history`, so anyone who can pull the image can read it. A secret mount
exposes the value only for the duration of one `RUN` instruction and writes
nothing to the layer.

```dockerfile
# WRONG: a build argument survives in the published image
FROM alpine:3.22
ARG REGISTRY_TOKEN
ENV REGISTRY_TOKEN=${REGISTRY_TOKEN}
RUN echo "fetching dependencies with $REGISTRY_TOKEN" > /tmp/build.log
# docker inspect myapp:1.0 --format '{{json .Config.Env}}'
# ["PATH=...","REGISTRY_TOKEN=fixture-token-value"]
```

```dockerfile
# syntax=docker/dockerfile:1.27
# CORRECT: the credential is mounted for one instruction only
FROM golang:1.27.1 AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN --mount=type=secret,id=netrc,target=/root/.netrc,mode=0400 \
    go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /out/server ./...
```

```bash
# Supply the secret from a file outside the build context
docker build --secret id=netrc,src="$HOME/.netrc" -t myapp:1.0 .

# Or take the value from an environment variable on the build client;
# it is mounted at /run/secrets/npm_token unless the RUN mount sets env=
docker build --secret id=npm_token,env=NPM_TOKEN -t myapp:1.0 .
```

Use `--mount=type=ssh` for private Git dependencies so the agent socket, not a
key file, is forwarded into the build.

### Security Scanning

Projects **MUST** scan images for vulnerabilities before deployment.

**Why**: Vulnerability scanning detects known CVEs in base images and
dependencies. Automated scanning in CI/CD prevents vulnerable images from
reaching production.

```bash
# Scan with Trivy
trivy image myapp:1.0

# Fail CI if critical vulnerabilities found
trivy image --severity CRITICAL,HIGH --exit-code 1 myapp:1.0

# Scan Dockerfile
trivy config Dockerfile
```

**CI Integration**:

```yaml
# GitHub Actions
- name: Scan image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: myapp:1.0
    severity: CRITICAL,HIGH
    exit-code: 1
```

### Hadolint for Dockerfile Linting

Projects **SHOULD** lint Dockerfiles with Hadolint.

```bash
# Install Hadolint
docker pull hadolint/hadolint

# Lint Dockerfile
docker run --rm -i hadolint/hadolint < Dockerfile

# Ignore specific rules
docker run --rm -i hadolint/hadolint \
  --ignore DL3008 --ignore DL3009 < Dockerfile
```

## Labels and Metadata

### Prometheus Discovery Labels

Projects **SHOULD** add Prometheus discovery labels to expose metrics.

**Why**: Labels enable automatic service discovery by Prometheus or other
monitoring tools. This eliminates manual configuration and enables dynamic
monitoring as services scale.

```yaml
services:
  api:
    labels:
      - "prometheus.io/scrape=true"
      - "prometheus.io/port=9090"
      - "prometheus.io/path=/metrics"
      - "prometheus.io/job=api"
```

### Traefik Integration Labels

Projects using Traefik **SHOULD** configure routing via labels.

```yaml
services:
  web:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.web.rule=Host(`example.com`)"
      - "traefik.http.routers.web.entrypoints=websecure"
      - "traefik.http.routers.web.tls.certresolver=letsencrypt"
      - "traefik.http.services.web.loadbalancer.server.port=80"
      - "traefik.http.routers.web.middlewares=security-headers@file"
```

### Container Metadata Labels

Projects **SHOULD** add metadata labels for documentation.

```yaml
services:
  app:
    labels:
      - "org.opencontainers.image.title=MyApp"
      - "org.opencontainers.image.version=1.0.0"
      - "org.opencontainers.image.authors=team@example.com"
      - "org.opencontainers.image.source=https://github.com/org/repo"
      - "com.example.team=platform"
      - "com.example.environment=production"
```

## Dependency Management

### depends_on with Health Checks

Projects **MUST** use `depends_on` with `condition: service_healthy`.

**Why**: Without health checks, `depends_on` only ensures start order, not
readiness. Using `service_healthy` ensures dependent services wait until
upstream services are actually ready to accept connections.

`depends_on` gates startup only. It does **NOT** provide runtime failure
recovery: `restart: true` restarts the dependent service when an explicit
Compose operation such as `docker compose restart` or `docker compose up`
updates or restarts the dependency. A dependency that crashes and is brought
back by its own restart policy does not trigger it, so applications **MUST**
reconnect with back-off rather than assume Compose will restart them.

```yaml
services:
  api:
    depends_on:
      database:
        condition: service_healthy
        # Restarts api when an explicit Compose operation restarts or
        # updates database; not on a crash or an automatic restart
        restart: true
      cache:
        condition: service_healthy
        restart: true

  database:
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 5s
      timeout: 3s
      retries: 5
```

### Graceful Shutdown

Projects **SHOULD** configure `stop_grace_period` for clean shutdowns.

**Why**: The default 10-second grace period may be insufficient for services to
drain connections, finish processing, or flush buffers. Proper grace periods
prevent data loss and connection errors.

```yaml
services:
  api:
    stop_grace_period: 30s  # Wait 30s before SIGKILL

  database:
    stop_grace_period: 60s  # Databases need more time
```

**Application Code**:

```python
import signal
import sys

def signal_handler(sig, frame):
    print("SIGTERM received, shutting down gracefully...")
    # Close database connections
    db.close()
    # Finish pending tasks
    task_queue.drain()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
```

## Environment-Specific Configurations

### Development Override

```yaml
# compose.override.yml (automatically loaded in development)
services:
  api:
    build:
      context: .
      target: development
    volumes:
      - ./src:/app/src  # Hot reload
    environment:
      - DEBUG=true
    ports:
      - "8080:8080"  # Expose for local debugging
```

### Production Configuration

```yaml
# compose.production.yml
services:
  api:
    image: registry.example.com/api@sha256:abc123...
    restart: always
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 1G
          cpus: '2'
    logging:
      driver: syslog
      options:
        syslog-address: "tcp://logs.example.com:514"
```

**Deployment**:

```bash
# Development (uses compose.yml + compose.override.yml)
docker compose up -d

# Production
docker compose -f compose.yml -f compose.production.yml up -d
```

## Complete Example

```yaml
# compose.yml - Production-ready configuration

# Optional sub-stacks
include:
  - compose.database.yml
  - compose.cache.yml
  - compose.monitoring.yml

# Reusable fragments
x-service-defaults: &service-defaults
  restart: unless-stopped
  init: true
  security_opt:
    - no-new-privileges:true
  cap_drop:
    - ALL

x-healthcheck-standard: &healthcheck-standard
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s
  start_interval: 2s

x-logging-standard: &logging-standard
  driver: json-file
  options:
    max-size: "50m"
    max-file: "5"

# Networks
networks:
  frontend:
    driver: bridge
  backend:
    internal: true

# Secrets
# Host files bind-mounted into the container: not encrypted, not in memory.
# Keep the source outside the build context, mode 0400, materialised by
# deployment tooling from a secret manager.
secrets:
  api_key:
    file: ${SECRETS_DIR:-/etc/myapp/secrets}/api_key

# Volumes
volumes:
  app-data:

# Services
services:
  api:
    # SHA256 digest pinning
    image: myapp/api@sha256:abc123def456...
    container_name: api
    <<: *service-defaults
    user: "1000:1000"
    read_only: true
    tmpfs:
      - /tmp
    logging:
      <<: *logging-standard
    networks:
      - frontend
      - backend
    depends_on:
      postgres:
        condition: service_healthy
        # Startup gating and explicit Compose operations only; the api
        # process reconnects with back-off if postgres restarts on its own
        restart: true
    secrets:
      - api_key
    environment:
      - API_KEY_FILE=/run/secrets/api_key
      - DATABASE_URL=postgres://user@postgres:5432/db
    volumes:
      - app-data:/data
    healthcheck:
      <<: *healthcheck-standard
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:8080/health"]
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1'
          pids: 100
        reservations:
          memory: 128M
    labels:
      # Prometheus discovery
      - "prometheus.io/scrape=true"
      - "prometheus.io/port=8080"
      - "prometheus.io/path=/metrics"
      # Metadata
      - "org.opencontainers.image.version=1.0.0"
```

## CI/CD Integration

### Build and Push

```yaml
# .github/workflows/docker.yml
name: Docker Build

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Scan image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ghcr.io/${{ github.repository }}:${{ github.sha }}
          severity: CRITICAL,HIGH
          exit-code: 1
```

### Compose Validation

```yaml
- name: Validate Compose files
  run: |
    docker compose config --quiet
    docker compose -f compose.yml -f compose.production.yml config --quiet
```

## Troubleshooting

### Container Logs

```bash
# Follow logs
docker compose logs -f api

# Last 100 lines
docker compose logs --tail=100 api

# Logs since timestamp
docker compose logs --since 2024-01-01T10:00:00 api

# All containers
docker compose logs -f
```

### Health Check Debugging

```bash
# Inspect health status
docker inspect api --format='{{.State.Health.Status}}'

# View health check logs
docker inspect api --format='{{json .State.Health.Log}}' | jq
```

### Network Debugging

```bash
# List networks
docker network ls

# Inspect network
docker network inspect frontend

# Test connectivity between containers
docker exec api ping -c 3 postgres
docker exec api nc -zv postgres 5432
```

### Resource Usage

```bash
# Real-time stats
docker stats

# Specific container
docker stats api

# Memory usage
docker stats --format "table {{.Name}}\t{{.MemUsage}}"
```

## See Also

- [Ansible Guide](ansible.md) - Configuration management and deployment
- [CI/CD Guide](../process/ci.md) - Continuous integration patterns
- [Testing Guide](../process/testing.md) - Container testing strategies

## References

- [Docker Engine 27.5 Release Notes](https://docs.docker.com/engine/release-notes/27/)
- [Docker Compose v5 Release Notes](https://docs.docker.com/compose/releases/release-notes/)
- [Manage Secrets in Docker Compose](https://docs.docker.com/compose/how-tos/use-secrets/)
- [Manage Sensitive Data with Docker Secrets (Swarm)](https://docs.docker.com/engine/swarm/secrets/)
- [Build Secrets](https://docs.docker.com/build/building/secrets/)
- [Start Containers Automatically](https://docs.docker.com/engine/containers/start-containers-automatically/)
- [Control Startup and Shutdown Order in Compose](https://docs.docker.com/compose/how-tos/startup-order/)
- [Kubernetes Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/)
- [Docker Compose Include Directive](https://docs.docker.com/compose/how-tos/multiple-compose-files/include/)
- [OWASP Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)
- [Docker Security Best Practices 2025](https://cloudnativenow.com/topics/cloudnativedevelopment/docker/docker-security-in-2025-best-practices-to-protect-your-containers-from-cyberthreats/)
- [Snyk Docker Security Best Practices](https://snyk.io/blog/10-docker-image-security-best-practices/)
- [Docker Image Digest Pinning](https://candrews.integralblue.com/2023/09/always-use-docker-image-digests/)
- [Docker Compose Modularity with Include](https://www.docker.com/blog/improve-docker-compose-modularity-with-include/)
- [Dockerfile Best Practices 2025](https://blog.bytescrum.com/dockerfile-best-practices-2025-secure-fast-and-modern)
