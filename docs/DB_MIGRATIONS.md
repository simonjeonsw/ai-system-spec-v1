# DB Migrations for Shadow + Learning Layers

## Migration file
- `sql/2026-02-15_shadow_learning_schema.sql`
- `sql/2026-02-16_stage_execution_ledger.sql`

## What it adds
- `video_uploads` optional execution columns:
  - `pipeline_profile`
  - `selected_hook_stage`
  - `shadow_toggles` (jsonb)
  - `hook_seed_path`
  - `hook_refined_path`
- `retention_events` table (append-only event store, idempotent via `event_key`)
- `learning_gates` table (latest decision per `video_id`, includes `policy_version`)
- `learning_gate_decisions` table (append-only decision history, idempotent via `decision_key`, includes `policy_version`)
- `stage_execution_ledger` table (deterministic stage-attempt ledger with unique key `(video_id, run_id, stage, attempt)`)

## Apply commands

### Option A) Supabase SQL Editor
1. Open Supabase Dashboard → SQL Editor.
2. Paste contents of `sql/2026-02-15_shadow_learning_schema.sql`.
3. Run both migration files in order.

### Option B) `psql`
```bash
psql "$SUPABASE_DB_URL" -f sql/2026-02-15_shadow_learning_schema.sql
psql "$SUPABASE_DB_URL" -f sql/2026-02-16_stage_execution_ledger.sql
```

## Verify commands
```bash
psql "$SUPABASE_DB_URL" -c "\d+ public.retention_events"
psql "$SUPABASE_DB_URL" -c "\d+ public.learning_gates"
psql "$SUPABASE_DB_URL" -c "\d+ public.learning_gate_decisions"
psql "$SUPABASE_DB_URL" -c "\d+ public.video_uploads"
psql "$SUPABASE_DB_URL" -c "\d+ public.stage_execution_ledger"
```

## Runtime note
`lib/analytics_collector.py` now attempts to persist:
- outcome snapshot events into `public.retention_events`
- learning gate outputs into `public.learning_gates` (latest status + `policy_version`)
- learning gate decision history into `public.learning_gate_decisions` (append-only + `policy_version`)

If tables are not present, collector continues non-blocking and prints warning lines.

`lib/pipeline_runner.py` now attempts to persist stage-level attempt checkpoints into
`public.stage_execution_ledger` via `lib.run_logger.emit_stage_execution_ledger()`.


## Idempotency keys
- `retention_events.event_key`: unique key for replay-safe outcome/feature writes.
- `learning_gate_decisions.decision_key`: unique key for replay-safe decision writes.


## Distributed lineage note
- Analytics outcome generation resolves `feature_snapshot` with DB-first lookup and local fallback.
- Local artifacts include `lineage_source` (`db|local|none`) for auditability.
- Outcome artifacts include `lineage_reason_code` (e.g., `db_hit`, `db_query_error+local_hit`) for deterministic fallback diagnostics.
