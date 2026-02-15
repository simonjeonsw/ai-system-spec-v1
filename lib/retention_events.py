"""Retention feature event helpers (Phase 4 shadow learning layer)."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List


RETENTION_EVENT_ARTIFACT_VERSION = "1.0"
RETENTION_EVENT_TYPE_FEATURE_SNAPSHOT = "feature_snapshot"
RETENTION_EVENT_TYPE_OUTCOME_SNAPSHOT = "outcome_snapshot"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _build_event_key(
    *,
    video_id: str,
    run_id: str,
    artifact_type: str,
    artifact_version: str,
    event_type: str,
    event_window: str,
    bucket: str,
) -> str:
    raw = "::".join([video_id, run_id, artifact_type, artifact_version, event_type, event_window, bucket])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_feature_snapshot_event(
    *,
    video_id: str,
    run_id: str,
    scene_contract_version: str,
    hook_payload: Dict[str, Any] | None,
    beat_payload: Dict[str, Any] | None,
    visual_beat_payload: Dict[str, Any] | None,
    shorts_payload: Dict[str, Any] | None,
) -> Dict[str, Any]:
    beats: List[Dict[str, Any]] = (beat_payload or {}).get("beat_graph", {}).get("beats", [])
    visual_beats: List[Dict[str, Any]] = (visual_beat_payload or {}).get("visual_beat_graph", {}).get("visual_beats", [])
    shorts_candidates: List[Dict[str, Any]] = (shorts_payload or {}).get("shorts_intelligence", {}).get("candidates", [])

    beat_density = min(1.0, len(beats) / 24.0)
    visual_beat_frequency = min(1.0, len(visual_beats) / max(len(beats), 1))

    energy_values = [
        _safe_float(beat.get("energy_curve_index"), 0.0)
        for beat in beats
        if isinstance(beat, dict)
    ]
    if not energy_values:
        energy_distribution = [0.0, 0.0, 0.0, 0.0]
    else:
        q1 = sum(1 for x in energy_values if x < 0.25) / len(energy_values)
        q2 = sum(1 for x in energy_values if 0.25 <= x < 0.5) / len(energy_values)
        q3 = sum(1 for x in energy_values if 0.5 <= x < 0.75) / len(energy_values)
        q4 = sum(1 for x in energy_values if x >= 0.75) / len(energy_values)
        energy_distribution = [round(q1, 4), round(q2, 4), round(q3, 4), round(q4, 4)]

    hook_type = ((hook_payload or {}).get("hook_hypothesis") or {}).get("hook_type", "unknown")

    source_beats = []
    for candidate in shorts_candidates:
        source_beats.extend(candidate.get("source_beat_ids", []))
    source_beats = sorted({str(x) for x in source_beats if x})

    prompt_hash_raw = "::".join(
        [
            str((hook_payload or {}).get("prompt_hash", "")),
            str((beat_payload or {}).get("prompt_hash", "")),
            str((visual_beat_payload or {}).get("prompt_hash", "")),
            str((shorts_payload or {}).get("prompt_hash", "")),
        ]
    )
    prompt_hash = hashlib.sha256(prompt_hash_raw.encode("utf-8")).hexdigest()

    artifact_type = "retention_feature_events"
    artifact_version = RETENTION_EVENT_ARTIFACT_VERSION
    event_type = RETENTION_EVENT_TYPE_FEATURE_SNAPSHOT
    event_window = "d_plus_3"

    return {
        "video_id": video_id,
        "run_id": run_id,
        "artifact_type": artifact_type,
        "artifact_version": artifact_version,
        "event_type": event_type,
        "event_window": event_window,
        "scoring_model_version": "retention_features_v1",
        "prompt_hash": prompt_hash,
        "scene_contract_version": scene_contract_version,
        "feature_snapshot": {
            "hook_type": hook_type,
            "beat_density": round(beat_density, 4),
            "visual_beat_frequency": round(visual_beat_frequency, 4),
            "energy_curve_distribution": energy_distribution,
            "shorts_extraction_source_beats": source_beats,
        },
        "outcome_metrics": {
            "ctr": None,
            "avd": None,
            "retention_curve_snapshots": [],
        },
        "created_at_utc": _now_iso(),
        "event_key": _build_event_key(
            video_id=video_id,
            run_id=run_id,
            artifact_type=artifact_type,
            artifact_version=artifact_version,
            event_type=event_type,
            event_window=event_window,
            bucket="feature_snapshot",
        ),
        "schema_version": RETENTION_EVENT_ARTIFACT_VERSION,
    }


def build_outcome_snapshot_event(
    *,
    video_id: str,
    run_id: str,
    scene_contract_version: str,
    ctr: float | None,
    avd: float | None,
    retention_curve_snapshots: List[Dict[str, Any]] | None = None,
    artifact_type: str | None = None,
    artifact_version: str | None = None,
    scoring_model_version: str | None = None,
    prompt_hash: str | None = None,
    feature_snapshot: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    resolved_prompt_hash = prompt_hash or hashlib.sha256(f"outcome::{video_id}::{run_id}".encode("utf-8")).hexdigest()
    resolved_artifact_type = artifact_type or "retention_feature_events"
    resolved_artifact_version = artifact_version or RETENTION_EVENT_ARTIFACT_VERSION
    event_type = RETENTION_EVENT_TYPE_OUTCOME_SNAPSHOT
    event_window = "d_plus_3"

    return {
        "video_id": video_id,
        "run_id": run_id,
        "artifact_type": resolved_artifact_type,
        "artifact_version": resolved_artifact_version,
        "event_type": event_type,
        "event_window": event_window,
        "scoring_model_version": scoring_model_version or "retention_features_v1",
        "prompt_hash": resolved_prompt_hash,
        "scene_contract_version": scene_contract_version,
        "feature_snapshot": feature_snapshot
        or {
            "hook_type": "unknown",
            "beat_density": 0.0,
            "visual_beat_frequency": 0.0,
            "energy_curve_distribution": [0.0, 0.0, 0.0, 0.0],
            "shorts_extraction_source_beats": [],
        },
        "outcome_metrics": {
            "ctr": ctr,
            "avd": avd,
            "retention_curve_snapshots": retention_curve_snapshots or [],
        },
        "created_at_utc": _now_iso(),
        "event_key": _build_event_key(
            video_id=video_id,
            run_id=run_id,
            artifact_type=resolved_artifact_type,
            artifact_version=resolved_artifact_version,
            event_type=event_type,
            event_window=event_window,
            bucket="outcome_snapshot",
        ),
        "schema_version": RETENTION_EVENT_ARTIFACT_VERSION,
    }
