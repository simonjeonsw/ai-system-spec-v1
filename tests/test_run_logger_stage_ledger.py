"""Regression tests for stage execution ledger logging."""

from __future__ import annotations

import importlib
import os
import unittest


class _FakeTable:
    def __init__(self, owner: "_FakeSupabase", table_name: str) -> None:
        self.owner = owner
        self.table_name = table_name

    def upsert(self, payload, on_conflict=None):
        self.owner.calls.append(
            {
                "table": self.table_name,
                "payload": payload,
                "on_conflict": on_conflict,
            }
        )
        return self

    def execute(self):
        self.owner.executed += 1
        return None


class _FakeSupabase:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.calls = []
        self.executed = 0

    def table(self, table_name: str):
        if self.should_fail:
            raise RuntimeError("supabase unavailable")
        return _FakeTable(self, table_name)




class _MissingTableSupabase:
    def __init__(self) -> None:
        self.calls = 0

    def table(self, _table_name: str):
        self.calls += 1
        raise RuntimeError("{'message':'Could not find the table 'public.stage_execution_ledger' in the schema cache','code':'PGRST205'}")


class StageExecutionLedgerRunLoggerTests(unittest.TestCase):
    def _load_run_logger(self):
        os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
        os.environ.setdefault("SUPABASE_KEY", "test-key")
        module = importlib.import_module("lib.run_logger")
        return importlib.reload(module)

    def test_emit_stage_execution_ledger_uses_deterministic_on_conflict_key(self) -> None:
        run_logger = self._load_run_logger()
        fake = _FakeSupabase()
        original = run_logger.supabase
        run_logger.supabase = fake
        try:
            run_logger.emit_stage_execution_ledger(
                video_id="vid001",
                run_id="run001",
                stage="research",
                attempt=2,
                status="success",
                metadata={"latency_ms": 123},
            )
        finally:
            run_logger.supabase = original

        self.assertEqual(fake.executed, 1)
        self.assertEqual(len(fake.calls), 1)
        call = fake.calls[0]
        self.assertEqual(call["table"], "stage_execution_ledger")
        self.assertEqual(call["on_conflict"], "video_id,run_id,stage,attempt")
        self.assertEqual(call["payload"]["video_id"], "vid001")
        self.assertEqual(call["payload"]["run_id"], "run001")
        self.assertEqual(call["payload"]["stage"], "research")
        self.assertEqual(call["payload"]["attempt"], 2)

    def test_emit_stage_execution_ledger_is_non_blocking_on_backend_error(self) -> None:
        run_logger = self._load_run_logger()
        fake = _FakeSupabase(should_fail=True)
        original = run_logger.supabase
        run_logger.supabase = fake
        try:
            run_logger.emit_stage_execution_ledger(
                video_id="vid001",
                run_id="run001",
                stage="planner",
                attempt=1,
                status="failure",
                error_summary="timeout",
            )
        finally:
            run_logger.supabase = original

    def test_missing_table_error_disables_future_attempts(self) -> None:
        run_logger = self._load_run_logger()
        missing = _MissingTableSupabase()
        original_supabase = run_logger.supabase
        original_disabled = run_logger._STAGE_LEDGER_DISABLED
        original_reason = run_logger._STAGE_LEDGER_DISABLE_REASON
        run_logger.supabase = missing
        run_logger._STAGE_LEDGER_DISABLED = False
        run_logger._STAGE_LEDGER_DISABLE_REASON = ""
        try:
            run_logger.emit_stage_execution_ledger(
                video_id="vid001",
                run_id="run001",
                stage="research",
                attempt=1,
                status="success",
            )
            self.assertTrue(run_logger._STAGE_LEDGER_DISABLED)
            self.assertEqual(run_logger._STAGE_LEDGER_DISABLE_REASON, "missing_table")
            first_calls = missing.calls
            run_logger.emit_stage_execution_ledger(
                video_id="vid001",
                run_id="run001",
                stage="research",
                attempt=2,
                status="success",
            )
            self.assertEqual(missing.calls, first_calls)
        finally:
            run_logger.supabase = original_supabase
            run_logger._STAGE_LEDGER_DISABLED = original_disabled
            run_logger._STAGE_LEDGER_DISABLE_REASON = original_reason


if __name__ == "__main__":
    unittest.main()
