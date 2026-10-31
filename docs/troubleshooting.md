# Troubleshooting and database operations

## Start and restart

Use the [installation guide](installation.md) for the Docker-only reviewer path or optional local Python path. Normal Docker restart preserves both named volumes:

```powershell
docker compose down
docker compose up --detach --wait app
```

If using AI, restart with the [AI profile command](local-llm.md#docker-setup-and-use) and retain `LLM_MODE=auto` on the app process. Stop local Uvicorn with Ctrl+C, then restart with its installation command.

## Common startup failures

- **Windows error 10048 / port occupied:** stop the prior app process in its terminal, or use `$env:APP_PORT='8001'` for Compose / `--port 8001` for local Uvicorn. Open the corresponding URL. Do not kill unrelated processes blindly.
- **Docker engine unavailable:** start Docker Desktop, select Linux containers, and wait for `docker version` to show the server.
- **Container startup/migration failure:** inspect `docker compose logs app`. Storage must be writable, file-backed SQLite. Do not delete a database to repair a migration without investigating and backing it up.
- **503 readiness:** `/health` only proves the process is alive. `/ready` also verifies schema revision and a rollback-only write. Check database URL, migrations, permissions, and space.
- **Demo login disabled:** local Python requires `DEMO_IDENTITY_MODE=header` for this exercise. The bare image defaults off; Compose enables demo headers explicitly. These identities are not real authentication.
- **Configuration appears ignored:** process environment overrides `.env`. Compose has its own internal database/LLM addresses. Restart the app after changing settings; editing a file does not change an already-running process.
- **AI errors:** follow the [LLM failure guide](local-llm.md#failures). Core readiness and human decisions do not depend on Ollama.

## Back up before maintenance

For a consistent manual demo backup, stop the app first so no writer holds the database. Local Python stores data at the configured `DATABASE_URL`, normally `data/mortgage_pricing.db`. Copy the stopped database to a protected backup location and verify the copy. Docker users can stop the app, then copy `/app/data/mortgage_pricing.db` out of its stopped container with `docker compose cp app:/app/data/mortgage_pricing.db <backup-path>` before removing containers. Keep backups outside Git and image build context.

For live backups or production operations, use SQLite's backup API or an approved database backup process rather than copying an active database without its transaction state. Verify `PRAGMA integrity_check` and `PRAGMA foreign_key_check` on a restored isolated copy and test the workflow. This release does not claim a production backup/restore drill.

## Deliberate demo reset

Reset erases requests, versions, decisions, assessments, and retry mappings. First stop the app and verify exactly which local database or Compose project is being reset. Preserve a backup if it may be needed. Resetting demo data is not part of ordinary installation or restart.

For **local Python**, remove only the explicitly chosen database file and its SQLite sidecars after stopping all writers, then run:

```powershell
uv run --locked python -m alembic upgrade head
uv run --locked python -m mortgage_pricing.seed
```

Verify migration head, integrity, fictional users/applications, and an empty request/history set before restarting. Do not recursively delete the whole repository or unrelated storage.

For **Docker**, `docker compose down` preserves volumes. `docker compose down --volumes` is destructive and also removes the selected project's model cache; do not use it for a database-only restart. A database-only reset requires explicitly identifying the `application-data` volume for the intended project, stopping its consumers, and removing that volume alone. Keep `model-cache` and all unrelated project volumes. The repository intentionally does not automatically reset evaluator databases.

Generated reports and local maintenance backups belong under gitignored `artifacts/`; model weights and databases must never enter source control.
