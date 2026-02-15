"""Hook shadow-layer generation utilities.

This module is intentionally non-blocking and feature-flag friendly:
- If generation fails, callers should continue the legacy pipeline.
- Outputs are schema-shaped so they can be logged and stored for future learning.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from .json_utils import ensure_schema_version, parse_json_with_repair
from .model_router import ModelRouter


DEFAULT_HOOK_SCHEMA_VERSION = "1.0"
DEFAULT_HOOK_SCORING_MODEL_VERSION = "hook_shadow_v1"


def _fallback_hook(video_id: str) -> Dict[str, Any]:
    base_text = f"What everyone misses about {video_id} could change your financial decisions this year."
    return {
        "video_id": video_id,
        "artifact_version": DEFAULT_HOOK_SCHEMA_VERSION,
        "scoring_model_version": DEFAULT_HOOK_SCORING_MODEL_VERSION,
        "prompt_hash": "fallback",
        "hook_hypothesis": {
            "hook_id": "hk-fallback-001",
            "hook_text": base_text,
            "hook_type": "curiosity",
            "curiosity_gap_score": 0.55,
            "emotional_trigger_tags": ["curiosity"],
            "power_keyword_tags": ["misses", "change"],
            "retention_prediction_score": 0.5,
            "confidence_score": 0.3,
        },
        "status": "degraded",
        "fallback_reason": "hook_generation_failed",
        "schema_version": DEFAULT_HOOK_SCHEMA_VERSION,
    }


def generate_hook_shadow(video_id: str) -> Dict[str, Any]:
    """Generate hook hypothesis object for shadow mode.

    This function should never raise; it returns a degraded fallback payload on any failure.
    """
    prompt = f"""
You are the Hook Generator agent in shadow mode.
Return JSON only with this schema:
{{
  "video_id": "{video_id}",
  "artifact_version": "1.0",
  "scoring_model_version": "hook_shadow_v1",
  "prompt_hash": "sha256 string",
  "hook_hypothesis": {{
    "hook_id": "hk-001",
    "hook_text": "...",
    "hook_type": "curiosity|fear|reward|contrarian|authority",
    "curiosity_gap_score": 0.0,
    "emotional_trigger_tags": ["..."],
    "power_keyword_tags": ["..."],
    "retention_prediction_score": 0.0,
    "confidence_score": 0.0
  }},
  "status": "ok",
  "fallback_reason": null,
  "schema_version": "1.0"
}}
Constraints:
- Output English only.
- Scores are floats in [0,1].
- Keep hook_text under 120 characters.
"""
    try:
        router = ModelRouter.from_env()
        response_text = router.generate_content(prompt)
        payload = parse_json_with_repair(response_text)
        ensure_schema_version(payload, DEFAULT_HOOK_SCHEMA_VERSION)
        payload.setdefault("artifact_version", DEFAULT_HOOK_SCHEMA_VERSION)
        payload.setdefault("scoring_model_version", DEFAULT_HOOK_SCORING_MODEL_VERSION)
        payload.setdefault("status", "ok")
        payload.setdefault("fallback_reason", None)
        payload.setdefault("video_id", video_id)
        if not payload.get("prompt_hash"):
            payload["prompt_hash"] = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        # ensure serializable and normalize unknown objects
        json.loads(json.dumps(payload, ensure_ascii=False))
        return payload
    except Exception:
        return _fallback_hook(video_id)
