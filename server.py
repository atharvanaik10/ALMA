from __future__ import annotations

import logging
from pathlib import Path
from time import perf_counter
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from alma.api.graph import graph_feature_collection
from alma.api.models import PlanRequest, PlanResponse
from alma.api.services import run_plan
from alma.logging_utils import configure_logging


configure_logging()
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="ALMA API", version="0.3.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/graph")
    def get_graph(graph_path: Optional[str] = Query(default=None)) -> JSONResponse:
        try:
            return JSONResponse(graph_feature_collection(graph_path))
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/plan", response_model=PlanResponse)
    def plan(payload: PlanRequest) -> PlanResponse:
        request_id = str(uuid4())[:8]
        started_at = perf_counter()
        last_progress: tuple[int, str] | None = None

        logger.info(
            "[plan:%s] started graph=%s time_steps=%s num_units=%s num_runs=%s",
            request_id,
            payload.graph_path or "default",
            payload.patrol.time_steps,
            payload.patrol.num_units,
            payload.eval.num_runs,
        )

        def log_progress(frac: float, message: str) -> None:
            nonlocal last_progress
            percent = max(0, min(100, int(round(frac * 100))))
            current = (percent, message)
            if current == last_progress:
                return
            last_progress = current
            logger.info("[plan:%s] %s%% %s", request_id, percent, message)

        try:
            artifacts = run_plan(payload, progress=log_progress)
        except FileNotFoundError as exc:
            elapsed = perf_counter() - started_at
            logger.warning("[plan:%s] failed after %.2fs: %s", request_id, elapsed, exc)
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception:
            elapsed = perf_counter() - started_at
            logger.exception("[plan:%s] failed after %.2fs", request_id, elapsed)
            raise
        elapsed = perf_counter() - started_at
        logger.info(
            "[plan:%s] completed in %.2fs schedule_rows=%s",
            request_id,
            elapsed,
            len(artifacts.schedule_json),
        )
        return PlanResponse(summary=artifacts.summary, schedule=artifacts.schedule_json)

    dist_path = Path(__file__).parent / "web" / "dist"
    if dist_path.exists():
        app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="static")

    return app


app = create_app()
