# AGENTS.md

## Purpose

This repository is a small research/demo application for ALMA patrol planning:

- `alma/`: core Python research library for graph loading, SSG solving, patrol simulation, and evaluation
- `alma/api/`: request models, graph serialization, and planning orchestration
- `server.py`: FastAPI entrypoint and static asset serving for `web/dist`
- `web/`: Svelte + Vite frontend
- `data/`: demo graph and input datasets

## Working Rules

- Prefer minimal, surgical changes. This repo is intentionally simple.
- Keep backend logic inside `alma/` and keep `server.py` thin.
- Treat `alma/` as the research core. Keep it simple, contained, and focused on the algorithmic pieces rather than UI or deployment concerns.
- Prefer putting HTTP glue, frontend state, and orchestration outside `alma/` when possible.
- Preserve the current API shape unless the task explicitly calls for API changes.
- Do not assume a system `python` binary exists. Use `python3` or `venv/bin/python`.
- Use `rg` for search and `npm run build` for frontend verification.

## Local Commands

- Backend dependency check:
  - `venv/bin/python -c "import fastapi, uvicorn, pandas, numpy; print('deps-ok')"`
- Backend syntax check:
  - `python3 -m compileall server.py alma`
- Frontend production build:
  - `cd web && npm run build`
- Local API server:
  - `venv/bin/python -m uvicorn server:app --reload`

## Deployment Notes

- The current Dockerfile is structured for a single Cloud Run container serving both the API and built frontend.
- `server.py` serves the frontend only when `web/dist` exists.
- The current API uses a synchronous `POST /plan` endpoint that returns the full payload in one response.
- The frontend should stay simple: show a spinner while the request runs, then render the returned schedule, efficiency metrics, and summary data.
- Avoid reintroducing in-memory job state unless there is a clear research need.
- If deploying to Cloud Run, prefer a single container with request-based billing and low minimum instances.

## Known Review Focus Areas

- `alma/api/services.py`: planning runtime cost from repeated evaluation sweeps
- `web/src/App.svelte`: client-side loading flow, schedule rendering, and long Google Maps route URLs for long schedules
- `server.py`: permissive CORS and static serving assumptions

## Change Expectations

- After backend changes, run at least the compile check.
- After frontend changes, run `npm run build`.
- Call out clearly if verification was limited by missing dependencies, sandbox restrictions, or long-running optimization paths.
