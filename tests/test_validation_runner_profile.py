"""Regression checks for profile-aware validation expectations."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
SAMPLE_DIR = REPO_ROOT / "spec" / "samples"
DATA_FIXTURE_DIR = REPO_ROOT / "data"


class ValidationRunnerProfileRegression(unittest.TestCase):
    def _write_manifest(self, video_id: str, shadow_toggles: dict[str, bool]) -> None:
        payload = {
            "video_id": video_id,
            "run_id": f"run-{video_id}",
            "pipeline_profile": "fixture",
            "shadow_toggles": shadow_toggles,
            "selected_hook_stage": "hook_seed",
            "files": {},
        }
        (DATA_DIR / f"{video_id}_pipeline.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _copy_stage_file(self, video_id: str, stage: str, sample_name: str, *, from_data_fixture: bool = False) -> None:
        source = (DATA_FIXTURE_DIR if from_data_fixture else SAMPLE_DIR) / sample_name
        target = DATA_DIR / f"{video_id}_{stage}.json"
        shutil.copyfile(source, target)

    def _run_validate_all(self, video_id: str, env_overrides: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if env_overrides:
            env.update(env_overrides)
        return subprocess.run(
            ["python", "-m", "lib.validation_runner", "all", "--url", video_id],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
        )

    def _cleanup_video_files(self, video_id: str) -> None:
        for path in DATA_DIR.glob(f"{video_id}_*.json"):
            path.unlink(missing_ok=True)

    def test_core_manifest_without_optional_shadow_artifacts_passes(self) -> None:
        video_id = "regcore001"
        self._cleanup_video_files(video_id)
        try:
            self._write_manifest(
                video_id,
                {
                    "HOOK_SHADOW_ENABLED": False,
                    "BEAT_SHADOW_ENABLED": False,
                    "VISUAL_BEAT_SHADOW_ENABLED": False,
                    "SHORTS_INTEL_SHADOW_ENABLED": False,
                    "RETENTION_EVENTS_ENABLED": False,
                },
            )
            self._copy_stage_file(video_id, "research", "Y-lFcCk0uEQ_research.json", from_data_fixture=True)
            self._copy_stage_file(video_id, "plan", "Y-lFcCk0uEQ_plan.json", from_data_fixture=True)
            self._copy_stage_file(video_id, "script", "Y-lFcCk0uEQ_script.json", from_data_fixture=True)
            self._copy_stage_file(video_id, "scenes", "Y-lFcCk0uEQ_scenes.json", from_data_fixture=True)

            result = self._run_validate_all(video_id, env_overrides={"PIPELINE_PROFILE": "full_shadow"})
            self.assertEqual(result.returncode, 0, msg=result.stderr)
        finally:
            self._cleanup_video_files(video_id)

    def test_full_shadow_manifest_missing_retention_events_fails(self) -> None:
        video_id = "regfull001"
        self._cleanup_video_files(video_id)
        try:
            self._write_manifest(
                video_id,
                {
                    "HOOK_SHADOW_ENABLED": True,
                    "BEAT_SHADOW_ENABLED": True,
                    "VISUAL_BEAT_SHADOW_ENABLED": True,
                    "SHORTS_INTEL_SHADOW_ENABLED": True,
                    "RETENTION_EVENTS_ENABLED": True,
                },
            )
            self._copy_stage_file(video_id, "research", "Y-lFcCk0uEQ_research.json", from_data_fixture=True)
            self._copy_stage_file(video_id, "plan", "Y-lFcCk0uEQ_plan.json", from_data_fixture=True)
            self._copy_stage_file(video_id, "script", "Y-lFcCk0uEQ_script.json", from_data_fixture=True)
            self._copy_stage_file(video_id, "scenes", "Y-lFcCk0uEQ_scenes.json", from_data_fixture=True)
            self._copy_stage_file(video_id, "hook", "hook_output_sample.json")
            self._copy_stage_file(video_id, "beat_graph", "beat_graph_output_sample.json")
            self._copy_stage_file(video_id, "visual_beat_graph", "visual_beat_graph_output_sample.json")
            self._copy_stage_file(video_id, "shorts_intelligence", "shorts_intelligence_output_sample.json")
            # intentionally omit retention_events file

            result = self._run_validate_all(video_id, env_overrides={"RETENTION_EVENTS_ENABLED": "false"})
            self.assertNotEqual(result.returncode, 0, msg="Validation unexpectedly passed")
            self.assertIn("Missing file for stage retention_events", result.stderr)
        finally:
            self._cleanup_video_files(video_id)


if __name__ == "__main__":
    unittest.main()
