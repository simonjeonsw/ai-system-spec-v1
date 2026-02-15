"""Shorts intelligence shadow layer.

Computes candidate feature vectors from beat/visual-beat shadow artifacts.
This is additive-only and must never block legacy shorts generation.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List


DEFAULT_SHORTS_ARTIFACT_VERSION = "1.0"
DEFAULT_SHORTS_SCORING_MODEL_VERSION = "shorts_intel_v1"


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


def _weighted_sum(features: Dict[str, float], weights: Dict[str, float]) -> float:
    return sum(weights.get(k, 0.0) * features.get(k, 0.0) for k in weights)


def _score_candidate(features: Dict[str, float]) -> float:
    weights = {
        "shock_value_score": 0.12,
        "emotion_peak_score": 0.11,
        "standalone_story_score": 0.11,
        "curiosity_gap_score": 0.10,
        "energy_curve_index": 0.08,
        "visual_intensity_score": 0.08,
        "knowledge_density_score": 0.08,
        "clip_independence_score": 0.10,
        "opening_velocity_score": 0.08,
        "pattern_interrupt_density": 0.06,
        "loop_potential_score": 0.08,
        "cognitive_load_index": -0.05,
        "drop_risk_prediction": -0.08,
    }
    base = _weighted_sum(features, weights)

    # non-linear drop risk penalty
    drop_risk = features.get("drop_risk_prediction", 0.0)
    nonlinear_penalty = 0.0
    if drop_risk > 0.5:
        nonlinear_penalty = 0.4 * ((drop_risk - 0.5) ** 2)

    # loop potential bonus
    loop_bonus = 0.0
    loop_potential = features.get("loop_potential_score", 0.0)
    if loop_potential > 0.7:
        loop_bonus = 0.12 * (loop_potential - 0.7)

    return _bounded(base - nonlinear_penalty + loop_bonus)


def generate_shorts_intelligence_shadow(
    video_id: str,
    beat_payload: Dict[str, Any],
    visual_beat_payload: Dict[str, Any] | None,
    run_id: str,
) -> Dict[str, Any]:
    beats: List[Dict[str, Any]] = (beat_payload.get("beat_graph") or {}).get("beats", [])
    visual_beats: List[Dict[str, Any]] = (visual_beat_payload or {}).get("visual_beat_graph", {}).get("visual_beats", [])
    visual_by_beat = {vb.get("parent_beat_id"): vb for vb in visual_beats if vb.get("parent_beat_id")}

    candidates = []
    for beat in beats:
        beat_id = beat.get("beat_id", "")
        visual = visual_by_beat.get(beat_id, {})

        features = {
            "shock_value_score": _bounded(float(beat.get("shock_value_score", 0.0))),
            "emotion_peak_score": _bounded(float(beat.get("emotion_peak_score", 0.0))),
            "standalone_story_score": _bounded(0.5 * float(beat.get("curiosity_gap_score", 0.0)) + 0.5 * float(beat.get("info_density_score", 0.0))),
            "curiosity_gap_score": _bounded(float(beat.get("curiosity_gap_score", 0.0))),
            "energy_curve_index": _bounded(float(beat.get("energy_curve_index", 0.0))),
            "visual_intensity_score": _bounded(float(visual.get("visual_intensity_score", 0.0))),
            "drop_risk_prediction": _bounded(float(beat.get("drop_risk_prediction", 0.0))),
            "knowledge_density_score": _bounded(float(beat.get("info_density_score", 0.0))),
            "clip_independence_score": _bounded(0.6 * float(beat.get("curiosity_gap_score", 0.0)) + 0.4 * float(beat.get("energy_curve_index", 0.0))),
            "opening_velocity_score": _bounded(1.0 - (int(beat.get("sequence_index", 1)) / max(len(beats), 1))),
            "pattern_interrupt_density": _bounded(float(visual.get("visual_intensity_score", 0.0)) * 0.8 + (0.2 if visual.get("motion_type") in {"camera_motion", "object_motion"} else 0.0)),
            "loop_potential_score": _bounded(0.5 * float(beat.get("curiosity_gap_score", 0.0)) + 0.5 * float(beat.get("shock_value_score", 0.0))),
            "cognitive_load_index": _bounded(float(beat.get("info_density_score", 0.0)) * 0.7 + float(beat.get("drop_risk_prediction", 0.0)) * 0.3),
        }
        score = _score_candidate(features)
        candidates.append(
            {
                "candidate_id": f"sc-{beat.get('sequence_index', 0):03d}",
                "source_beat_ids": [beat_id],
                "source_visual_beat_ids": [visual.get("visual_beat_id")] if visual.get("visual_beat_id") else [],
                "features": features,
                "composite_score": score,
                "shorts_candidate_flag": score >= 0.55,
                "shorts_rank_priority": 0,
            }
        )

    ranked = sorted(candidates, key=lambda c: c["composite_score"], reverse=True)
    for idx, cand in enumerate(ranked, start=1):
        cand["shorts_rank_priority"] = idx if cand["shorts_candidate_flag"] else 0

    prompt_hash = hashlib.sha256(f"shorts_intel_shadow::{video_id}".encode("utf-8")).hexdigest()
    return {
        "video_id": video_id,
        "run_id": run_id,
        "artifact_version": DEFAULT_SHORTS_ARTIFACT_VERSION,
        "scoring_model_version": DEFAULT_SHORTS_SCORING_MODEL_VERSION,
        "prompt_hash": prompt_hash,
        "scene_contract_version": "legacy_scene_v1",
        "shorts_intelligence": {
            "version": DEFAULT_SHORTS_ARTIFACT_VERSION,
            "candidates": candidates,
        },
        "schema_version": DEFAULT_SHORTS_ARTIFACT_VERSION,
    }
