# DB Migrations for Shadow + Learning Layers

## Migration file
- `sql/2026-02-15_shadow_learning_schema.sql`

## What it adds
- `video_uploads` optional execution columns:
  - `pipeline_profile`
  - `selected_hook_stage`
  - `shadow_toggles` (jsonb)
  - `hook_seed_path`
  - `hook_refined_path`
- `retention_events` table (append-only event store)
- `learning_gates` table (latest decision per `video_id`)
- `learning_gate_decisions` table (append-only decision history with lineage join keys)

## Apply commands

### Option A) Supabase SQL Editor
1. Open Supabase Dashboard → SQL Editor.
2. Paste contents of `sql/2026-02-15_shadow_learning_schema.sql`.
3. Run.

### Option B) `psql`
```bash
psql "$SUPABASE_DB_URL" -f sql/2026-02-15_shadow_learning_schema.sql
```

## Verify commands
```bash
psql "$SUPABASE_DB_URL" -c "\d+ public.retention_events"
psql "$SUPABASE_DB_URL" -c "\d+ public.learning_gates"
psql "$SUPABASE_DB_URL" -c "\d+ public.learning_gate_decisions"
psql "$SUPABASE_DB_URL" -c "\d+ public.video_uploads"
```

## Runtime note
`lib/analytics_collector.py` now attempts to persist:
- outcome snapshot events into `public.retention_events`
- learning gate outputs into `public.learning_gates` (latest status)
- learning gate decision history into `public.learning_gate_decisions` (append-only)

If tables are not present, collector continues non-blocking and prints warning lines.
