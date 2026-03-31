from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from alma.api.services import resolve_graph_path
from alma.data import load_graph_for_animation


def _load_address_map(graph_path: Path) -> dict[str, Any]:
    with graph_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {
        str(node_id): attrs.get("address")
        for node_id, attrs in data.items()
        if isinstance(attrs, dict) and "address" in attrs
    }


def graph_feature_collection(graph_path: Optional[str] = None) -> dict[str, Any]:
    resolved_path = resolve_graph_path(graph_path)
    nodes, edges = load_graph_for_animation(resolved_path)
    address_map = _load_address_map(resolved_path)

    features: list[dict[str, Any]] = []
    for idx, edge in enumerate(edges):
        p1, p2 = edge
        features.append(
            {
                "type": "Feature",
                "id": idx,
                "properties": {},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [list(p1), list(p2)],
                },
            }
        )

    for node_id, coords in nodes.items():
        features.append(
            {
                "type": "Feature",
                "properties": {"node_id": node_id, "address": address_map.get(str(node_id))},
                "geometry": {"type": "Point", "coordinates": [coords[0], coords[1]]},
            }
        )

    return {"type": "FeatureCollection", "features": features}
