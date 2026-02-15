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


DEFAULT_HOOK_SCHEMA_VERSION = "1.1"
DEFAULT_HOOK_SCORING_MODEL_VERSION = "hook_shadow_v2"


def _safe_script_excerpt(script_payload: Dict[str, Any] | None, max_chars: int = 280) -> str:
    if not script_payload:
        return ""
    raw = str(script_payload.get("script") or script_payload.get("full_script") or "")
    cleaned = " ".join(raw.split())
    return cleaned[:max_chars]


def _safe_research_context(research_payload: Dict[str, Any] | None) -> Dict[str, Any]:
    if not research_payload:
        return {
            "key_claims": [],
            "target_audience": "",
            "thesis": "",
        }
    claims = research_payload.get("claims") or []
    if isinstance(claims, list):
        claim_texts = [str(c.get("claim") if isinstance(c, dict) else c) for c in claims[:3]]
    else:
        claim_texts = []
    return {
        "key_claims": [text for text in claim_texts if text],
        "target_audience": str(research_payload.get("target_audience") or ""),
        "thesis": str(research_payload.get("core_thesis") or research_payload.get("thesis") or ""),
    }


def _fallback_hook(video_id: str, *, generated_from_stage: str, source_artifact_refs: Dict[str, str]) -> Dict[str, Any]:
    base_text = f"What everyone misses about {video_id} could change your financial decisions this year."
    return {
        "video_id": video_id,
        "artifact_version": DEFAULT_HOOK_SCHEMA_VERSION,
        "scoring_model_version": DEFAULT_HOOK_SCORING_MODEL_VERSION,
        "prompt_hash": "fallback",
        "generated_from_stage": generated_from_stage,
        "source_artifact_refs": source_artifact_refs,
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


def _render_prompt(
    *,
    video_id: str,
    generated_from_stage: str,
    research_payload: Dict[str, Any] | None,
    script_payload: Dict[str, Any] | None,
) -> str:
    research_context = _safe_research_context(research_payload)
    script_excerpt = _safe_script_excerpt(script_payload)

    return f"""
You are the Hook Generator agent in shadow mode.
Return JSON only with this schema:
{{
  "video_id": "{video_id}",
  "artifact_version": "{DEFAULT_HOOK_SCHEMA_VERSION}",
  "scoring_model_version": "{DEFAULT_HOOK_SCORING_MODEL_VERSION}",
  "prompt_hash": "sha256 string",
  "generated_from_stage": "{generated_from_stage}",
  "source_artifact_refs": {{
    "research": "research_payload|none",
    "script_long": "script_long_payload|none"
  }},
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
  "schema_version": "{DEFAULT_HOOK_SCHEMA_VERSION}"
}}
Constraints:
- Output English only.
- Scores are floats in [0,1].
- Keep hook_text under 120 characters.
- If context is sparse, still provide one high-confidence hypothesis with transparent confidence score.

Context:
- video_id: {video_id}
- generated_from_stage: {generated_from_stage}
- research_key_claims: {json.dumps(research_context.get("key_claims", []), ensure_ascii=False)}
- research_target_audience: {research_context.get("target_audience", "")}
- research_thesis: {research_context.get("thesis", "")}
- script_opening_excerpt: {script_excerpt}
"""


def generate_hook_shadow(
    video_id: str,
    *,
    generated_from_stage: str = "seed",
    research_payload: Dict[str, Any] | None = None,
    script_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Generate hook hypothesis object for shadow mode.

    This function should never raise; it returns a degraded fallback payload on any failure.
    """
    source_artifact_refs = {
        "research": "research_payload" if research_payload else "none",
        "script_long": "script_long_payload" if script_payload else "none",
    }
    prompt = _render_prompt(
        video_id=video_id,
        generated_from_stage=generated_from_stage,
        research_payload=research_payload,
        script_payload=script_payload,
    )
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
        payload.setdefault("generated_from_stage", generated_from_stage)
        payload.setdefault("source_artifact_refs", source_artifact_refs)
        if not payload.get("prompt_hash"):
            payload["prompt_hash"] = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        # ensure serializable and normalize unknown objects
        json.loads(json.dumps(payload, ensure_ascii=False))
        return payload
    except Exception:
        return _fallback_hook(
            video_id,
            generated_from_stage=generated_from_stage,
            source_artifact_refs=source_artifact_refs,
        )


def generate_hook_seed(video_id: str) -> Dict[str, Any]:
    return generate_hook_shadow(video_id, generated_from_stage="seed")


def generate_hook_refined(
    video_id: str,
    research_payload: Dict[str, Any] | None,
    script_payload: Dict[str, Any] | None,
) -> Dict[str, Any]:
    return generate_hook_shadow(
        video_id,
        generated_from_stage="refined",
        research_payload=research_payload,
        script_payload=script_payload,
    )
