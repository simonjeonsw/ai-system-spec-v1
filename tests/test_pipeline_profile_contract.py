"""Contract regression tests for pipeline profile resolver."""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_profile_probe(env_overrides: dict[str, str]) -> dict[str, object]:
    env = os.environ.copy()
    env.update(
        {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_KEY": "test-key",
        }
    )
    env.update(env_overrides)
    probe = (
        "import json; "
        "from lib.pipeline_runner import resolve_pipeline_profile; "
        "name,toggles=resolve_pipeline_profile(); "
        "print(json.dumps({'profile_name':name,'toggles':toggles}, sort_keys=True))"
    )
    completed = subprocess.run(
        ["python", "-c", probe],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    return json.loads(lines[-1])


class PipelineProfileContractRegression(unittest.TestCase):
    def test_core_profile_returns_stable_tuple_contract_shape(self) -> None:
        payload = _run_profile_probe({"PIPELINE_PROFILE": "core"})
        self.assertEqual(payload["profile_name"], "core")
        toggles = payload["toggles"]
        self.assertIsInstance(toggles, dict)
        self.assertEqual(
            sorted(toggles.keys()),
            sorted(
                [
                    "HOOK_SHADOW_ENABLED",
                    "BEAT_SHADOW_ENABLED",
                    "VISUAL_BEAT_SHADOW_ENABLED",
                    "SHORTS_INTEL_SHADOW_ENABLED",
                    "RETENTION_EVENTS_ENABLED",
                ]
            ),
        )

    def test_explicit_toggle_override_beats_profile_default(self) -> None:
        payload = _run_profile_probe(
            {
                "PIPELINE_PROFILE": "core",
                "HOOK_SHADOW_ENABLED": "true",
                "RETENTION_EVENTS_ENABLED": "1",
            }
        )
        toggles = payload["toggles"]
        self.assertTrue(toggles["HOOK_SHADOW_ENABLED"])
        self.assertTrue(toggles["RETENTION_EVENTS_ENABLED"])

    def test_unknown_profile_falls_back_to_none_with_false_toggles(self) -> None:
        payload = _run_profile_probe({"PIPELINE_PROFILE": "unknown_profile"})
        self.assertEqual(payload["profile_name"], "none")
        self.assertTrue(all(value is False for value in payload["toggles"].values()))

    def test_pipeline_runner_no_longer_contains_dict_compat_branch(self) -> None:
        source = (REPO_ROOT / "lib" / "pipeline_runner.py").read_text(encoding="utf-8")
        self.assertNotIn("Unexpected pipeline profile resolution payload", source)
        self.assertNotIn("isinstance(profile_resolution, dict)", source)

    def test_validation_runner_uses_same_profile_policy(self) -> None:
        probe = (
            "import json; "
            "from lib.pipeline_profile import TOGGLE_STAGE_MAP, resolve_pipeline_profile_from_env; "
            "from lib.validation_runner import _resolve_expected_stages; "
            "_,toggles=resolve_pipeline_profile_from_env(); "
            "expected={'research','plan','script','scenes'}; "
            "[expected.add(stage) for name,stage in TOGGLE_STAGE_MAP.items() if toggles.get(name)]; "
            "print(json.dumps({'policy_expected':sorted(expected),'validation_expected':sorted(_resolve_expected_stages('no_manifest_video'))}))"
        )
        env = os.environ.copy()
        env.update({
            "PIPELINE_PROFILE": "full_shadow",
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_KEY": "test-key",
        })
        completed = subprocess.run(
            ["python", "-c", probe],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
        payload = json.loads(lines[-1])
        self.assertEqual(payload["policy_expected"], payload["validation_expected"])


if __name__ == "__main__":
    unittest.main()
