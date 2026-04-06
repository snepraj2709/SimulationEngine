# Backend

FastAPI backend for the Decision Simulation Engine.

## Key capabilities

- JWT auth
- Safe URL intake with SSRF checks
- Deterministic URL fetching and HTML extraction
- OpenAI-driven product understanding, ICP generation, and scenario generation
- Deterministic simulation engine with explainable outcomes
- Feedback persistence
- PostgreSQL persistence with Alembic migrations

## Commands

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# set OPENAI_API_KEY in .env before creating analyses
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

If you run the backend directly from your host shell, `DATABASE_URL` in `.env` should use
`localhost:5432`. The hostname `db` only resolves inside the Docker Compose network.

`OPENAI_API_KEY` is required for real URL analysis. `OPENAI_MODEL` defaults to `gpt-5.4`.
