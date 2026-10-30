# Troubleshooting and local data

## Docker and startup

- If `docker compose` cannot connect, start Docker Desktop and wait for its Linux container engine to become ready.
- If the default port is occupied, set `APP_PORT` to an unused host port, restart the app, and open the matching `127.0.0.1` URL. Compose binds to loopback.
- If image or package downloads fail, restore access to the configured registries or use an existing cache. The first uncached build was not verified offline.
- If the container exits before serving, inspect `docker compose logs app`. Startup requires writable file-backed SQLite and applies migrations and seeds before starting Uvicorn.
- `/health` reports process liveness; `/ready` checks usable, migrated storage. Core mode has no model service. AI/model settings and cache checks are deferred to Phase 09.
- No minimum CPU, memory, or disk specification has been measured. When Docker reports resource exhaustion, free host resources or adjust Docker Desktop allocation and retry.

## Local Python startup

The direct Python run needs Python 3.12, the locked dependencies, and access to package registries for uncached packages. Its database is `data/mortgage_pricing.db`. Stop Uvicorn with Ctrl+C and restart using the README’s local Python commands; the database and history remain on disk.

## Stop, restart, and reset

For Compose, `docker compose down` stops the service and preserves its named application-data volume. Restart with `docker compose up --detach --wait`; use `docker compose up --build --detach --wait` after changing the image source. For Python, Ctrl+C stops the server without removing the local database.

**Destructive reset:** `docker compose down --volumes` removes the active Compose project’s named volume and permanently deletes its database, requests, decisions, and history. Run it only for a deliberately disposable demo after checking the project name and data. Never use it to fix routine startup problems. Application startup and seeding do not reset evaluator data.
