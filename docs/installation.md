# Installation and startup

## Recommended reviewer path: Docker only

Requirements: Docker Desktop/Engine with Linux containers and Docker Compose v2, a browser, and the extracted repository. Git is optional because a repository ZIP works. Python, uv, Node, and a host Ollama installation are not needed. Docker Desktop's official [Windows instructions](https://docs.docker.com/desktop/setup/install/windows-install/) describe its supported backends; start Docker and wait for the engine before continuing.

Check installation:

```powershell
docker version
docker compose version
```

From the repository root, start the core demo:

```powershell
docker compose up --build --detach --wait app
```

Open `http://127.0.0.1:8000/`. One non-root application container serves UI and API, migrates SQLite, and explicitly seeds fictional demo users/applications. It has a read-only root filesystem, a writable named data volume, dropped Linux capabilities, loopback-only publishing, and bounded logs. `/health` is process liveness; `/ready` requires migrated, writable storage. Neither requires a model.

To add AI:

```powershell
$env:LLM_MODE = 'auto'
docker compose --profile ai up --build --detach
docker compose --profile ai logs --follow model-init
```

The AI profile pulls Ollama's official image and automatically downloads the selected model into `model-cache` if needed. The app remains usable while setup runs or if it fails. After the job prints ready, enable AI in the reviewer screen. Details and troubleshooting are in [local LLM](local-llm.md). A cached restart needs the local images and model cache; an uncached first build/download needs network access.

On bash, use `LLM_MODE=auto docker compose --profile ai up --build -d` instead of the PowerShell environment assignment. The provided Compose path uses CPU inference; hardware acceleration is deployment-specific and is not required for the human workflow.

## Configuration

No `.env` file is needed for the default Docker demo. If local overrides are needed, copy `.env.example` to `.env` and edit it. Process environment overrides `.env`. Compose explicitly sets its container database, demo identity, and internal Ollama URL, so a host Python URL is not accidentally used inside the app container.

| Setting | Local Python default | Compose demo |
| --- | --- | --- |
| `APP_ENV` | `development` | `production` process configuration |
| `DATABASE_URL` | `sqlite:///./data/mortgage_pricing.db` | `/app/data` in `application-data` |
| `DEMO_IDENTITY_MODE` | `off` | `header` (demo only) |
| `SEED_DEMO_DATA` | `false` | `true` at container startup |
| `LLM_MODE` | `off` | `off`; set `auto` explicitly for AI |
| `LLM_BASE_URL` | `http://127.0.0.1:11434` | `http://ollama:11434` |
| `LLM_TIMEOUT_SECONDS` | 30 | `COMPOSE_LLM_TIMEOUT_SECONDS`, default 120 |
| `APP_PORT` | Uvicorn CLI flag | Host port, default 8000 |

`APP_PORT` is a Compose setting; local Uvicorn takes `--host` and `--port` explicitly. `COMPOSE_LLM_BASE_URL` can override the internal runtime URL for an intentional external deployment. The generation deadline covers queueing, streaming, and one repair; runtime digest discovery is separately bounded to at most five seconds. Secrets and `.env` are excluded from Git and Docker build context.

## Optional developer path: local Python/Uvicorn

Install Python 3.12 and [uv](https://docs.astral.sh/uv/getting-started/installation/). Node is needed only for UI tests. From the repository root:

```powershell
uv sync --locked
New-Item -ItemType Directory -Force data | Out-Null
$env:DEMO_IDENTITY_MODE = 'header'
uv run --locked python -m alembic upgrade head
uv run --locked python -m mortgage_pricing.seed
uv run --locked python -m uvicorn mortgage_pricing.main:create_app --factory --host 127.0.0.1 --port 8000
```

Keep that terminal open. Stop with Ctrl+C. Startup through Uvicorn does not automatically migrate or seed; the preceding commands do. Repeating seed adds missing fictional records without resetting submitted requests. The bare Docker image and generic startup default to no demo identity and no demo seeding; Compose opts into both explicitly.

For local Python AI, follow the [native Ollama alternative](local-llm.md#native-ollama-alternative), or use a deliberately configured reachable runtime. The Compose Ollama service has no published host port by default.

## Updating an existing installation

Stop the app before taking a database backup, update the checkout, and rebuild with `docker compose up --build --detach --wait app` (or the AI profile command if using AI). Preserve the named volumes. Startup applies additive migrations and does not reset data. Local Python users run `uv sync --locked` and `alembic upgrade head` before restarting Uvicorn. Review [release evidence](build-log.md) and [production requirements](production-notes.md) before a real deployment.
