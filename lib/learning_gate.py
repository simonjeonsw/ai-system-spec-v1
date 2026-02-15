"""Learning gate evaluator for retention feedback loops.

Rule (default): require 2 consecutive outcome snapshots meeting baselines
before recommending model/prompt promotion.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _load_outcome_events(video_id: str) -> List[Dict[str, Any]]:
    data_dir = Path(__file__).resolve().parent.parent / "data"
    path = data_dir / f"{video_id}_retention_events.json"
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

    events = payload.get("events", []) if isinstance(payload, dict) else []
    filtered = []
    for event in events:
        if not isinstance(event, dict):
            continue
        if event.get("event_type") != "outcome_snapshot":
            continue
        filtered.append(event)
    return filtered


def evaluate_learning_gate(
    *,
    video_id: str,
    ctr_baseline: float = 5.0,
    avd_baseline: float = 40.0,
    rework_ctr_floor: float = 4.0,
    rework_avd_floor: float = 35.0,
    min_consecutive: int = 2,
) -> Dict[str, Any]:
    outcomes = _load_outcome_events(video_id)
    latest = outcomes[-min_consecutive:] if len(outcomes) >= min_consecutive else outcomes

    signals = []
    for event in latest:
        metrics = event.get("outcome_metrics", {})
        ctr = _safe_float(metrics.get("ctr"))
        avd = _safe_float(metrics.get("avd"))
        signals.append(
            {
                "created_at_utc": event.get("created_at_utc"),
                "run_id": event.get("run_id"),
                "artifact_type": event.get("artifact_type"),
                "artifact_version": event.get("artifact_version"),
                "ctr": ctr,
                "avd": avd,
                "meets_publish": bool(ctr is not None and avd is not None and ctr >= ctr_baseline and avd >= avd_baseline),
                "meets_rework": bool(ctr is not None and avd is not None and (ctr < rework_ctr_floor or avd < rework_avd_floor)),
            }
        )

    promote = len(signals) >= min_consecutive and all(s["meets_publish"] for s in signals[-min_consecutive:])
    rework = len(signals) >= min_consecutive and all(s["meets_rework"] for s in signals[-min_consecutive:])

    decision = "hold"
    action = "collect_more_data"
    if promote:
        decision = "promote"
        action = "allow_learning_update"
    elif rework:
        decision = "rework"
        action = "block_learning_update_and_revise_assets"

    lineage_source = signals[-1] if signals else {}
    payload = {
        "video_id": video_id,
        "decision": decision,
        "action": action,
        "policy": {
            "ctr_baseline": ctr_baseline,
            "avd_baseline": avd_baseline,
            "rework_ctr_floor": rework_ctr_floor,
            "rework_avd_floor": rework_avd_floor,
            "min_consecutive": min_consecutive,
        },
        "window_size": min_consecutive,
        "evaluated_outcomes": len(signals),
        "signals": signals,
        "lineage": {
            "run_id": lineage_source.get("run_id"),
            "artifact_type": lineage_source.get("artifact_type"),
            "artifact_version": lineage_source.get("artifact_version"),
        },
        "schema_version": "1.1",
    }

    data_dir = Path(__file__).resolve().parent.parent / "data"
    out_path = data_dir / f"{video_id}_learning_gate.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload
