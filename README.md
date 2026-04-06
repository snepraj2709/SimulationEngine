# Decision Simulation Engine

Production-ready MVP web app for Growth, Product, Pricing, and Strategy teams. Submit a company or product URL and the app:

- extracts product and pricing signals
- normalizes product understanding into structured JSON
- generates 3 to 5 ICPs
- proposes realistic scenarios
- simulates deterministic ICP reactions
- aggregates churn, downgrade, upgrade, retention, revenue, and perception outcomes
- captures thumbs up/down feedback for simulation usefulness

The repository is split into:

- `backend/`: FastAPI modular monolith, PostgreSQL, Alembic, deterministic analysis + simulation pipeline
- `frontend/`: React + Vite analytics UI with charts and React Flow reasoning visualization
- `docker-compose.yml`: one-command local stack

See the backend and frontend READMEs plus the setup and deployment guide in the project handoff.
