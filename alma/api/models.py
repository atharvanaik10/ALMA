from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class GameParamsModel(BaseModel):
    alpha: float = Field(default=1.0, ge=0.0)
    beta: float = Field(default=1.0, ge=0.0)
    gamma: float = Field(default=1.0, ge=0.0)
    delta: float = Field(default=1.0, ge=0.0)
    resource_budget: float = Field(default=10.0, gt=0.0)


class PatrolParamsModel(BaseModel):
    time_steps: int = Field(default=480, ge=1, le=10_000)
    num_units: int = Field(default=5, ge=1, le=1_000)
    pick_diverse_start_nodes: bool = True
    start_index: int = Field(default=0, ge=0)
    random_seed: int = Field(default=0, ge=0)


class EvalParamsModel(BaseModel):
    p_event: float = Field(default=0.3, ge=0.0, le=1.0)
    num_runs: int = Field(default=200, ge=1, le=10_000)


class PlanRequest(BaseModel):
    graph_path: Optional[str] = Field(default=None)
    game: GameParamsModel = Field(default_factory=GameParamsModel)
    patrol: PatrolParamsModel = Field(default_factory=PatrolParamsModel)
    eval: EvalParamsModel = Field(default_factory=EvalParamsModel)


class ScheduleRow(BaseModel):
    time_step: int
    unit_id: int
    node_id: str


class PlanResponse(BaseModel):
    summary: dict[str, Any]
    schedule: list[ScheduleRow] = Field(default_factory=list)
