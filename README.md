# ALMA: Active Law‑enforcement Mixed‑strategy Allocator

Risk‑aware patrol planning for the UIUC/Champaign area using Stackelberg Security Games (SSG).

This repository is intentionally simple: a small, well-documented Python research library (`alma/`), a thin FastAPI server (`server.py`), and a minimal Svelte+Tailwind UI in `web/`.

## Project Layout

-   `alma/`: Core research library for graph I/O, SSG solve, patrol simulation, and evaluation.
-   `server.py`: Thin FastAPI app that wires the API together and serves `web/dist` after a build.
-   `alma/api/`: Small API layer for request models, graph serialization, and planning orchestration.
-   Caching: Repeated runs with the same inputs are loaded from `cache/` automatically (see below).
-   `web/`: Minimal Svelte + Tailwind app (single page) that calls the API and renders a MapLibre map and schedule.
-   `data/`: Sample graph JSON (`uiuc_graph.json`).

Removed legacy scaffolding (complex backend, SvelteKit app, Streamlit scripts) to keep the POC easy to read and extend.

## Quick Start

### Python setup

```bash
python -m venv venv && source venv/bin/activate  # optional
pip install -r requirements.txt
```

### Start the API

```bash
uvicorn server:app --reload
```

API will run on `http://localhost:8000`.

By default the server loads `data/uiuc_graph.json`. Override it with:

```bash
export ALMA_GRAPH_PATH=data/uiuc_graph.json
```

### Web UI

Use this for dev:

```bash
cd web
npm install
npm run dev
```

Use this for prof:

```bash
cd web
npm install
npm run build           # outputs to web/dist
cd ..
uvicorn server:app --reload   # serves web/dist at /
```

Open `http://localhost:8000` for the integrated app, or `http://localhost:5173` during frontend development.

## API

Current API:

-   `GET /healthz` — Lightweight health check.
-   `GET /graph` — Graph as GeoJSON FeatureCollection for the map.
-   `POST /plan?mode=main` — Run the main planning pipeline synchronously and return the core result payload.
-   `POST /plan?mode=efficiency` — Run only the optional efficiency-by-units comparison sweep.

The frontend uses a two-phase flow while keeping a single planning route:

-   First call `POST /plan?mode=main` and render everything that is ready immediately: summary, schedule, baseline metrics, and main evaluation outputs.
-   If the user selected the optional efficiency comparison graph, automatically follow with `POST /plan?mode=efficiency`.
-   While the second call is running, only the chart area shows a loading spinner. The rest of the page stays usable with the main results already visible.

This keeps the implementation small while avoiding separate job state, polling, or streaming complexity.

Example plan request body:

The UI now exposes a single unit-count control labeled as the number of patrol units. That value drives both `game.resource_budget` and `patrol.num_units`; the resource budget is interpreted as the number of available patrol units rather than as a separate independent budget.

```json
{
	"game": {
		"alpha": 1,
		"beta": 1,
		"gamma": 1,
		"delta": 1,
		"resource_budget": 5
	},
	"patrol": {
		"time_steps": 120,
		"num_units": 5,
		"start_index": 0,
		"random_seed": 0
	},
	"eval": {
		"p_event": 0.3,
		"num_runs": 200
	}
}
```

## Library (`alma/`)

Key modules:

-   `config.py`: Typed parameter objects (`GameParams`, `PatrolParams`).
-   `data.py`: Graph I/O and helpers for animation/visualization.
-   `ssg.py`: Stackelberg Security Game solver (CVXPY/ECOS/OSQP).
-   `patrol.py`: Transition matrix and patrol simulation.
-   `schedule.py`: High‑level orchestration that wires everything.
-   `cli.py`: Simple CLI to export schedules as CSV.
-   `api/services.py`: Shared backend planning/evaluation path used by the API.

Example usage:

```python
from alma.config import GameParams, PatrolParams
from alma.schedule import generate_patrol_schedule

game = GameParams(alpha=1, beta=1, gamma=1, delta=1, resource_budget=5)
patrol = PatrolParams(time_steps=120, num_units=5, start_index=0, random_seed=0)
df, summary = generate_patrol_schedule('data/uiuc_graph.json', game, patrol)
print(df.head(), summary)
```

CLI:

```bash
python -m alma.cli --graph data/uiuc_graph.json --output patrol_schedule.csv --time-steps 120 --num-units 5
```

## Notes

-   The UI is intentionally lean: one page, simple form, spinner-based loading state, and a compact table.
-   The UI no longer exposes separate resource budget and patrol-unit controls. One unit-count input drives both `game.resource_budget` and `patrol.num_units`.
-   In this repo, interpret the resource budget as the number of patrol units available to the defender.
-   If you’re iterating on research (utility functions, constraints, solver behavior), concentrate changes inside `alma/`.
-   Keep `alma/` small and contained as the research core. Prefer putting frontend concerns, HTTP glue, request orchestration, and deployment behavior outside the research package when possible.
-   The target deployment path is a single `POST /plan` route with query-controlled modes rather than job polling or background workers.

## Setup (Data Prep)

The demo expects a road graph with risk attached from a processed crime log. Run the one‑time setup CLI to build these artifacts.

### Requirements

-   Python packages (install on your env):
    -   `pip install osmnx openai python-dotenv`
-   API keys (available as environment variables or in a `.env` file):
    -   `GOOGLE_MAPS_API_KEY`: for geocoding the crime log locations
    -   `OPENAI_API_KEY`: for classifying crime severities (1–5)

### Commands

-   Process the raw crime log (writes `data/crime_log_processed_location.csv` and `data/crime_log_processed.csv`):

    ```bash
    # Edit configuration constants near the top of alma/setup.py first.
    python -m alma.setup
    ```

-   Build the road graph and risk (writes `data/uiuc_graph.json` and preview images in `assets/`):

    ```bash
    # Set RUN_MODE = "build-graph" in alma/setup.py, then run:
    python -m alma.setup
    ```

-   Run both steps in sequence:

    ```bash
    # Set RUN_MODE = "all" in alma/setup.py, then run:
    python -m alma.setup
    ```

The setup script does not currently accept CLI flags. Configure paths and `RUN_MODE` in `alma/setup.py`, then run `python -m alma.setup`. It fails fast if dependencies or API keys are missing so you can fix configuration early.

### Caching behavior

-   The solver/simulation is cached on disk under `cache/` keyed by the graph file content and the parameter values.
-   Cache is automatic via `generate_patrol_schedule_cached(...)`.
-   The app retains only the 10 most recent schedule caches (`schedule_*.csv` + `summary_*.json`) and evicts older pairs automatically.
-   `reverse_geocode_cache.json` is separate and is not pruned automatically because it avoids repeat Google Maps API calls during setup.

## Deployment Notes

For a simple hosted demo, Cloud Run is a good fit because one container can serve both the built frontend and the FastAPI backend.

### Local container run

```bash
docker build -t alma .
docker run --rm -p 8080:8080 alma
```

Open `http://localhost:8080`.

### Cloud Run deploy

Build and push with Google Cloud Build:

```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/alma
```

Deploy to Cloud Run:

```bash
gcloud run deploy alma \
  --image gcr.io/PROJECT_ID/alma \
  --platform managed \
  --region REGION \
  --allow-unauthenticated \
  --set-env-vars ALMA_GRAPH_PATH=data/uiuc_graph.json
```

Recommended defaults for a low-cost personal demo:

-   `min-instances=0`
-   small memory/CPU
-   accept cold starts between demos

If you want CI/CD from GitHub, the simplest path is to connect the repository to Cloud Build or Cloud Run source deployment and let Google rebuild and redeploy on each push. That keeps the deploy flow aligned with this repo's goal of staying small and research-focused.
