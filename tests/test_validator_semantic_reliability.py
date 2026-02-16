"""Regression checks for semantic overlap reliability guards."""

from __future__ import annotations

import unittest

from lib.validator import ScriptValidator


class ValidatorSemanticReliabilityTests(unittest.TestCase):
    def test_sparse_keyword_signal_does_not_raise_overlap_critical(self) -> None:
        research_payload = {
            "executive_summary": "A short update.",
            "key_facts": ["Single fact."],
            "viewer_takeaway": "Watch updates.",
            "sources": [],
        }
        script_payload = {
            "script": "간단한 요약입니다.",
            "citations": [],
            "schema_version": "1.0",
        }
        validator = ScriptValidator(research_payload, script_payload)
        result = validator.semantic_consistency_check(metadata_payload=None, scene_output=None)
        overlap_errors = [e for e in result["errors"] if "Semantic overlap too low" in e]
        self.assertEqual(overlap_errors, [])


if __name__ == "__main__":
    unittest.main()
