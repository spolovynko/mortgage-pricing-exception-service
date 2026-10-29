# Database migrations

Run migrations through Alembic with `DATABASE_URL` set to the intended SQLite URL:

```powershell
$env:DATABASE_URL = "sqlite:///./data/mortgage_pricing.db"
uv run --locked python -m alembic upgrade head
```

Tests inject a temporary database URL through Alembic's configuration attributes.
Do not use `Base.metadata.create_all()` for operational schema setup.
