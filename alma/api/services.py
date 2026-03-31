from __future__ import annotations

import csv
import io
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from alma import GameParams, PatrolParams
from alma.api.models import PlanRequest
from alma.data import get_node_list_and_risk, load_graph
from alma.evaluator import (
    compute_schedule_metrics,
    evaluate_schedule,
    generate_uniform_schedule,
)
from alma.schedule import generate_patrol_schedule_cached

DEFAULT_GRAPH_PATH = "data/uiuc_graph.json"


@dataclass(frozen=True)
class PlanArtifacts:
    summary: dict[str, Any]
    schedule_json: list[dict[str, Any]]
    schedule_csv: str


def resolve_graph_path(graph_path: Optional[str] = None) -> Path:
    configured = graph_path or os.getenv("ALMA_GRAPH_PATH") or DEFAULT_GRAPH_PATH
    path = Path(configured)
    if not path.exists():
        raise FileNotFoundError(f"Graph JSON not found: {path}")
    return path


def _schedule_to_json(df) -> list[dict[str, Any]]:
    return [
        {
            "time_step": int(r["time_step"]),
            "unit_id": int(r["unit_id"]),
            "node_id": str(r["node_id"]),
        }
        for r in df.to_dict(orient="records")
    ]


def _schedule_to_csv(schedule_json: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["time_step", "unit_id", "node_id"])
    writer.writeheader()
    for row in schedule_json:
        writer.writerow(row)
    return buf.getvalue()


def run_plan(
    payload: PlanRequest,
    progress: Optional[Callable[[float, str], None]] = None,
) -> PlanArtifacts:
    def report(frac: float, message: str) -> None:
        if progress is None:
            return
        progress(max(0.0, min(1.0, float(frac))), message)

    graph_path = resolve_graph_path(payload.graph_path)
    game = GameParams(**payload.game.model_dump())
    patrol = PatrolParams(**payload.patrol.model_dump())

    df, summary = generate_patrol_schedule_cached(
        graph_path,
        game,
        patrol,
        progress=lambda frac, message: report(0.05 + 0.75 * frac, message),
    )
    graph = load_graph(graph_path)
    node_list, risk = get_node_list_and_risk(graph)

    report(0.85, "Evaluating policy...")
    eval_ssg = evaluate_schedule(
        df,
        node_list,
        risk,
        time_steps=patrol.time_steps,
        p_event=payload.eval.p_event,
        num_runs=payload.eval.num_runs,
        seed=patrol.random_seed,
    )
    det_ssg = compute_schedule_metrics(df, node_list)

    report(0.90, "Evaluating baseline...")
    df_uniform = generate_uniform_schedule(
        graph,
        node_list,
        time_steps=patrol.time_steps,
        num_units=patrol.num_units,
        seed=patrol.random_seed,
    )
    eval_uni = evaluate_schedule(
        df_uniform,
        node_list,
        risk,
        time_steps=patrol.time_steps,
        p_event=payload.eval.p_event,
        num_runs=payload.eval.num_runs,
        seed=patrol.random_seed,
    )
    det_uni = compute_schedule_metrics(df_uniform, node_list)

    sweep_max = min(6, max(1, patrol.num_units))
    units_list = list(range(1, sweep_max + 1))
    ssg_means: list[float] = []
    uni_means: list[float] = []
    for index, units in enumerate(units_list, start=1):
        report(0.92 + 0.06 * (index / len(units_list)), f"Comparing {units} patrol unit(s)...")
        patrol_variant = PatrolParams(
            time_steps=patrol.time_steps,
            num_units=units,
            start_index=patrol.start_index,
            random_seed=patrol.random_seed,
        )
        df_ssg, _ = generate_patrol_schedule_cached(graph_path, game, patrol_variant)
        ssg_means.append(
            float(
                evaluate_schedule(
                    df_ssg,
                    node_list,
                    risk,
                    time_steps=patrol.time_steps,
                    p_event=payload.eval.p_event,
                    num_runs=payload.eval.num_runs,
                    seed=patrol.random_seed,
                ).get("efficiency_mean", 0.0)
            )
        )
        df_uniform_variant = generate_uniform_schedule(
            graph,
            node_list,
            time_steps=patrol.time_steps,
            num_units=units,
            seed=patrol.random_seed,
        )
        uni_means.append(
            float(
                evaluate_schedule(
                    df_uniform_variant,
                    node_list,
                    risk,
                    time_steps=patrol.time_steps,
                    p_event=payload.eval.p_event,
                    num_runs=payload.eval.num_runs,
                    seed=patrol.random_seed,
                ).get("efficiency_mean", 0.0)
            )
        )

    summary.update(
        {
            "efficiency_ssg_mean": float(eval_ssg.get("efficiency_mean", 0.0)),
            "efficiency_ssg_std": float(eval_ssg.get("efficiency_std", 0.0)),
            "efficiency_uniform_mean": float(eval_uni.get("efficiency_mean", 0.0)),
            "efficiency_uniform_std": float(eval_uni.get("efficiency_std", 0.0)),
            "p_event": float(payload.eval.p_event),
            "num_runs": float(payload.eval.num_runs),
            "eff_by_units_units": units_list,
            "eff_by_units_ssg": ssg_means,
            "eff_by_units_uniform": uni_means,
            "movement_ssg_total_hops": det_ssg["movement_total_hops"],
            "movement_ssg_by_unit_hops": det_ssg["movement_by_unit_hops"],
            "coverage_ssg_total_ratio": det_ssg["coverage_total_ratio"],
            "coverage_ssg_total_count": det_ssg["coverage_total_count"],
            "coverage_ssg_total_nodes": det_ssg["coverage_total_nodes"],
            "coverage_ssg_by_unit_ratio": det_ssg["coverage_by_unit_ratio"],
            "coverage_ssg_by_unit_count": det_ssg["coverage_by_unit_count"],
            "movement_uniform_total_hops": det_uni["movement_total_hops"],
            "movement_uniform_by_unit_hops": det_uni["movement_by_unit_hops"],
            "coverage_uniform_total_ratio": det_uni["coverage_total_ratio"],
            "coverage_uniform_total_count": det_uni["coverage_total_count"],
            "coverage_uniform_total_nodes": det_uni["coverage_total_nodes"],
            "coverage_uniform_by_unit_ratio": det_uni["coverage_by_unit_ratio"],
            "coverage_uniform_by_unit_count": det_uni["coverage_by_unit_count"],
        }
    )

    schedule_json = _schedule_to_json(df)
    schedule_csv = _schedule_to_csv(schedule_json)
    report(1.0, "Done")
    return PlanArtifacts(summary=summary, schedule_json=schedule_json, schedule_csv=schedule_csv)
