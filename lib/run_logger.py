"""Run-log utilities for pipeline observability."""

from __future__ import annotations

import sys
import uuid
from typing import Any, Dict, Optional

from .supabase_client import supabase


def build_metrics(
    *,
    latency_ms: int = 0,
    tokens: int = 0,
    cost_usd: float = 0.0,
    cache_hit: bool = False,
    retry_count: int = 0,
) -> Dict[str, Any]:
    return {
        "latency_ms": latency_ms,
        "tokens": tokens,
        "cost_usd": cost_usd,
        "cache_hit": cache_hit,
        "retry_count": retry_count,
    }


def emit_run_log(
    *,
    stage: str,
    status: str,
    input_refs: Optional[Dict[str, Any]] = None,
    output_refs: Optional[Dict[str, Any]] = None,
    metrics: Optional[Dict[str, Any]] = None,
    error_summary: Optional[str] = None,
    attempts: int = 0,
    run_id: Optional[str] = None,
) -> str:
    """Insert a pipeline_runs record and return the run_id."""
    metrics_payload = metrics or {}
    required_keys = {"latency_ms", "tokens", "cost_usd", "cache_hit", "retry_count"}
    if not required_keys.issubset(metrics_payload.keys()):
        missing = required_keys - set(metrics_payload.keys())
        raise ValueError(f"Missing required metrics keys: {sorted(missing)}")
    run_id = run_id or str(uuid.uuid4())
    payload = {
        "run_id": run_id,
        "stage": stage,
        "status": status,
        "attempts": attempts,
        "input_refs": input_refs or {},
        "output_refs": output_refs or {},
        "error_summary": error_summary,
        "metrics": metrics_payload,
    }
    try:
        supabase.table("pipeline_runs").insert(payload).execute()
    except Exception as exc:  # Avoid crashing on logging failures.
        print(f"Run log insert failed: {exc}", file=sys.stderr)
    return run_id


def emit_stage_execution_ledger(
    *,
    video_id: str,
    run_id: str,
    stage: str,
    attempt: int,
    status: str,
    error_summary: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Persist deterministic stage execution checkpoints.

    Uniqueness contract: (video_id, run_id, stage, attempt)
    """

    payload: Dict[str, Any] = {
        "video_id": video_id,
        "run_id": run_id,
        "stage": stage,
        "attempt": attempt,
        "status": status,
        "error_summary": error_summary,
        "metadata": metadata or {},
    }
    try:
        supabase.table("stage_execution_ledger").upsert(
            payload,
            on_conflict="video_id,run_id,stage,attempt",
        ).execute()
    except Exception as exc:
        print(f"Stage execution ledger upsert failed: {exc}", file=sys.stderr)
