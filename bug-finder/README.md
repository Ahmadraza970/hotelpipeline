# Bug Finder

> Find and fix bugs across **any** codebase — lint-level findings plus an AI reviewer, each with a previewed fix diff you apply with confidence.

A web app: paste / upload / (soon) connect a repo → get ranked bug findings → preview an AI-generated unified-diff fix → download patch or open a PR.

## Stack

- **Frontend** — React 18 + TypeScript + Vite + Tailwind + Monaco editor
- **Backend** — FastAPI + pydantic
- **Detection** — `ruff` (Python), `eslint`/`tsc` (JS/TS, optional via `INSTALL_NODE=true`), plus an **LLM judge** (OpenAI-compatible) for semantic bugs that linters miss
- **Fixing** — LLM emits a **unified diff**, never a whole-file rewrite; re-linted before "Apply" is offered
- **Deploy** — Docker Compose (api + nginx static frontend)

## Run locally (dev)

```bash
# Backend (lint-only; no LLM key needed)
cd bug-finder/backend
cp .env.example .env
pip install -r requirements.txt
# optional: pip install ruff  (piped automatically via requirements.txt)
uvicorn app.main:app --reload --port 8000

# Frontend
cd ../frontend
npm install
npm run dev     # http://localhost:5173
```

Add `LLM_API_KEY` to `backend/.env` (and optionally `LLM_BASE_URL`/`LLM_MODEL`) for AI findings and
the fix generator — these are gated behind the **Pro** plan in the UI (`/pricing`).
Without it the app still scans lint-only. A local `bf_premium` flag simulates the plan
so the Pro flow is testable before billing ships in v1.1.

## Run with Docker

```bash
docker compose up --build       # api :8000  |  web :80
```

Set `VITE_API_URL` in compose for the browser origin. Project state is persisted under `./data/projects`.

## Architecture

```
input (paste/upload/github) -> Stage A linters -> Stage B LLM judge (clean files only)
                              -> dedupe + severity ranking -> findings list
fix click -> LLM unified diff -> apply -> re-lint gate -> diff preview
export -> unified patch / GitHub PR
```

## Docs

See `plans/bug-finder-prd.md` for the full product spec and UX wireframes.
