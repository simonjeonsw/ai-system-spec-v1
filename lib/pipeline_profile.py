"""Shared pipeline profile policy and toggle resolution helpers."""

from __future__ import annotations

import os
from typing import Dict, Final, Mapping


HOOK_SHADOW_ENABLED_ENV: Final = "HOOK_SHADOW_ENABLED"
BEAT_SHADOW_ENABLED_ENV: Final = "BEAT_SHADOW_ENABLED"
VISUAL_BEAT_SHADOW_ENABLED_ENV: Final = "VISUAL_BEAT_SHADOW_ENABLED"
SHORTS_INTEL_SHADOW_ENABLED_ENV: Final = "SHORTS_INTEL_SHADOW_ENABLED"
RETENTION_EVENTS_ENABLED_ENV: Final = "RETENTION_EVENTS_ENABLED"
PIPELINE_PROFILE_ENV: Final = "PIPELINE_PROFILE"

TOGGLE_ENV_NAMES: Final[tuple[str, ...]] = (
    HOOK_SHADOW_ENABLED_ENV,
    BEAT_SHADOW_ENABLED_ENV,
    VISUAL_BEAT_SHADOW_ENABLED_ENV,
    SHORTS_INTEL_SHADOW_ENABLED_ENV,
    RETENTION_EVENTS_ENABLED_ENV,
)

PIPELINE_PROFILES: Final[Mapping[str, Mapping[str, bool]]] = {
    "core": {
        HOOK_SHADOW_ENABLED_ENV: False,
        BEAT_SHADOW_ENABLED_ENV: False,
        VISUAL_BEAT_SHADOW_ENABLED_ENV: False,
        SHORTS_INTEL_SHADOW_ENABLED_ENV: False,
        RETENTION_EVENTS_ENABLED_ENV: False,
    },
    "shadow": {
        HOOK_SHADOW_ENABLED_ENV: True,
        BEAT_SHADOW_ENABLED_ENV: True,
        VISUAL_BEAT_SHADOW_ENABLED_ENV: True,
        SHORTS_INTEL_SHADOW_ENABLED_ENV: True,
        RETENTION_EVENTS_ENABLED_ENV: False,
    },
    "full_shadow": {
        HOOK_SHADOW_ENABLED_ENV: True,
        BEAT_SHADOW_ENABLED_ENV: True,
        VISUAL_BEAT_SHADOW_ENABLED_ENV: True,
        SHORTS_INTEL_SHADOW_ENABLED_ENV: True,
        RETENTION_EVENTS_ENABLED_ENV: True,
    },
}

TOGGLE_STAGE_MAP: Final[Mapping[str, str]] = {
    HOOK_SHADOW_ENABLED_ENV: "hook",
    BEAT_SHADOW_ENABLED_ENV: "beat_graph",
    VISUAL_BEAT_SHADOW_ENABLED_ENV: "visual_beat_graph",
    SHORTS_INTEL_SHADOW_ENABLED_ENV: "shorts_intelligence",
    RETENTION_EVENTS_ENABLED_ENV: "retention_events",
}

_TRUTHY_ENV_VALUES: Final[set[str]] = {"1", "true", "yes", "on"}


def parse_bool_env(value: str | None) -> bool:
    return (value or "").strip().lower() in _TRUTHY_ENV_VALUES


def resolve_pipeline_profile_from_env(env: Mapping[str, str] | None = None) -> tuple[str, Dict[str, bool]]:
    """Resolve active profile and shadow toggles deterministically.

    Precedence: explicit env override > profile default > hardcoded false.
    """

    env_map = os.environ if env is None else env
    requested_profile = str(env_map.get(PIPELINE_PROFILE_ENV, "")).strip().lower()
    profile_defaults = PIPELINE_PROFILES.get(requested_profile, {})

    resolved_toggles: Dict[str, bool] = {}
    for toggle_name in TOGGLE_ENV_NAMES:
        explicit_env_value = env_map.get(toggle_name)
        if explicit_env_value is not None:
            resolved_toggles[toggle_name] = parse_bool_env(explicit_env_value)
            continue
        if toggle_name in profile_defaults:
            resolved_toggles[toggle_name] = bool(profile_defaults[toggle_name])
            continue
        resolved_toggles[toggle_name] = False

    resolved_profile = requested_profile if requested_profile in PIPELINE_PROFILES else "none"
    return resolved_profile, resolved_toggles

