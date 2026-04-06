# Backend

FastAPI backend for the Decision Simulation Engine.

## Key capabilities

- JWT auth
- Safe URL intake with SSRF checks
- Heuristic scraping and product understanding
- Deterministic ICP generation and scenario generation
- Deterministic simulation engine with explainable outcomes
- Feedback persistence
- PostgreSQL persistence with Alembic migrations

## Commands

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

If you run the backend directly from your host shell, `DATABASE_URL` in `.env` should use
`localhost:5432`. The hostname `db` only resolves inside the Docker Compose network.
