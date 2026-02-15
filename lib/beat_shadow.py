"""Deterministic Beat/Visual Beat shadow generation utilities.

These helpers are intentionally non-blocking and side-channel only.
They must not mutate legacy scene/script behavior.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List


DEFAULT_BEAT_ARTIFACT_VERSION = "1.0"
DEFAULT_BEAT_SCORING_MODEL_VERSION = "beat_shadow_v1"
DEFAULT_VISUAL_BEAT_SCORING_MODEL_VERSION = "visual_beat_shadow_v1"

_NARRATIVE_ROLE_CYCLE = ["hook", "escalation", "reveal", "conflict", "twist", "resolution"]


def _split_sentences(script_text: str) -> List[str]:
    raw = re.split(r"(?<=[.!?])\s+", script_text or "")
    cleaned = [s.strip() for s in raw if s and s.strip()]
    return cleaned[:40]


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


def _score_sentence(sentence: str, index: int, total: int) -> Dict[str, float]:
    words = sentence.split()
    length = len(words)
    has_number = bool(re.search(r"\d", sentence))
    has_question = "?" in sentence
    has_contrast = bool(re.search(r"\bbut\b|\bhowever\b|\byet\b", sentence, re.IGNORECASE))

    shock = 0.35 + (0.2 if has_contrast else 0.0) + (0.1 if has_number else 0.0)
    curiosity = 0.3 + (0.3 if has_question else 0.0)
    density = min(1.0, length / 28)
    emotion = 0.25 + (0.2 if "!" in sentence else 0.0) + (0.1 if has_question else 0.0)
    energy = 1.0 - abs((index / max(total, 1)) - 0.35)
    drop_risk = 0.2 + (0.3 if length > 38 else 0.0) + (0.2 if length < 6 else 0.0)

    return {
        "emotion_peak_score": _bounded(emotion),
        "shock_value_score": _bounded(shock),
        "curiosity_gap_score": _bounded(curiosity),
        "info_density_score": _bounded(density),
        "energy_curve_index": _bounded(energy),
        "drop_risk_prediction": _bounded(drop_risk),
    }


def generate_beat_graph_shadow(video_id: str, script_payload: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    script_text = str(script_payload.get("script", ""))
    sentences = _split_sentences(script_text)
    if not sentences:
        sentences = ["No script content available for beat shadow generation."]

    beats = []
    total = len(sentences)
    for idx, sentence in enumerate(sentences, start=1):
        role = _NARRATIVE_ROLE_CYCLE[(idx - 1) % len(_NARRATIVE_ROLE_CYCLE)]
        base_scores = _score_sentence(sentence, idx, total)
        beats.append(
            {
                "beat_id": f"b-{idx:03d}",
                "sequence_index": idx,
                "narrative_role_tag": role,
                "script_span_ref": {
                    "start_char": max(0, script_text.find(sentence)),
                    "end_char": max(0, script_text.find(sentence)) + len(sentence),
                },
                **base_scores,
                "shorts_candidate_flag": base_scores["drop_risk_prediction"] < 0.65 and base_scores["shock_value_score"] > 0.4,
                "shorts_rank_priority": 0,
            }
        )

    # derive rank priority deterministically
    ranked = sorted(
        beats,
        key=lambda b: (
            b["drop_risk_prediction"],
            -(0.4 * b["shock_value_score"] + 0.3 * b["curiosity_gap_score"] + 0.3 * b["emotion_peak_score"]),
        ),
    )
    for priority, beat in enumerate(ranked, start=1):
        beat["shorts_rank_priority"] = priority if beat["shorts_candidate_flag"] else 0

    prompt_hash = hashlib.sha256(f"beat_shadow::{video_id}".encode("utf-8")).hexdigest()
    return {
        "video_id": video_id,
        "run_id": run_id,
        "artifact_version": DEFAULT_BEAT_ARTIFACT_VERSION,
        "scoring_model_version": DEFAULT_BEAT_SCORING_MODEL_VERSION,
        "prompt_hash": prompt_hash,
        "scene_contract_version": "legacy_scene_v1",
        "beat_graph": {"version": DEFAULT_BEAT_ARTIFACT_VERSION, "beats": beats},
        "schema_version": DEFAULT_BEAT_ARTIFACT_VERSION,
    }


def generate_visual_beat_graph_shadow(video_id: str, beat_payload: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    beats = (beat_payload.get("beat_graph") or {}).get("beats", [])
    visual_beats: List[Dict[str, Any]] = []
    seq = 1
    for beat in beats:
        intensity = _bounded(0.5 * beat.get("shock_value_score", 0.0) + 0.5 * beat.get("emotion_peak_score", 0.0))
        motion_type = "camera_motion" if intensity >= 0.65 else "micro_motion"
        if beat.get("drop_risk_prediction", 0.0) >= 0.7:
            motion_type = "object_motion"
        expected_duration = 2.2 if intensity >= 0.7 else 2.8
        visual_beats.append(
            {
                "visual_beat_id": f"vb-{seq:03d}",
                "parent_beat_id": beat.get("beat_id"),
                "sequence_index": seq,
                "visual_intensity_score": intensity,
                "motion_type": motion_type,
                "expected_duration_seconds": expected_duration,
            }
        )
        seq += 1

    prompt_hash = hashlib.sha256(f"visual_beat_shadow::{video_id}".encode("utf-8")).hexdigest()
    return {
        "video_id": video_id,
        "run_id": run_id,
        "artifact_version": DEFAULT_BEAT_ARTIFACT_VERSION,
        "scoring_model_version": DEFAULT_VISUAL_BEAT_SCORING_MODEL_VERSION,
        "prompt_hash": prompt_hash,
        "scene_contract_version": "legacy_scene_v1",
        "visual_beat_graph": {"version": DEFAULT_BEAT_ARTIFACT_VERSION, "visual_beats": visual_beats},
        "schema_version": DEFAULT_BEAT_ARTIFACT_VERSION,
    }
