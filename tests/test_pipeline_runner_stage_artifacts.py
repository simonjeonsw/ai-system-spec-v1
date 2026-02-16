"""Regression checks for stage-marker stripping helpers in pipeline runner."""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


class PipelineRunnerStageArtifactRegression(unittest.TestCase):
    def _run_probe(self, script: str) -> dict[str, object]:
        env = os.environ.copy()
        env.update(
            {
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_KEY": "test-key",
            }
        )
        completed = subprocess.run(
            ["python", "-c", script],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
        return json.loads(lines[-1])

    def test_strip_stage_artifacts_removes_known_markers_without_nameerror(self) -> None:
        probe = (
            "import json; "
            "from lib.pipeline_runner import _strip_stage_artifacts; "
            "text='[HOOK] Intro. [BEAT] Data point. [VISUAL_BEAT] Cue. [SHORTS_INTEL] Rank.'; "
            "cleaned=_strip_stage_artifacts(text); "
            "print(json.dumps({'cleaned':cleaned}))"
        )
        payload = self._run_probe(probe)
        cleaned = str(payload["cleaned"])
        self.assertNotIn("[HOOK]", cleaned)
        self.assertNotIn("[BEAT]", cleaned)
        self.assertIn("Intro.", cleaned)
        self.assertIn("Data point.", cleaned)

    def test_split_text_into_beats_handles_stage_markers(self) -> None:
        probe = (
            "import json; "
            "from lib.pipeline_runner import _split_text_into_beats; "
            "text='[HOOK] First sentence. [BEAT] Second sentence with extra words for chunking.'; "
            "beats=_split_text_into_beats(text, max_words=6); "
            "print(json.dumps({'beats':beats}))"
        )
        payload = self._run_probe(probe)
        beats = payload["beats"]
        self.assertIsInstance(beats, list)
        self.assertGreaterEqual(len(beats), 1)
        joined = " ".join(str(item) for item in beats)
        self.assertNotIn("[HOOK]", joined)
        self.assertNotIn("[BEAT]", joined)


if __name__ == "__main__":
    unittest.main()
