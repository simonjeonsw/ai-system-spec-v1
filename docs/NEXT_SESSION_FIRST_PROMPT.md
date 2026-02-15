You are continuing work on the repository `ai-system-spec-v1` in production-hardening mode.

## Context
- Priority-A hardening is already implemented:
  - lineage persist to `video_uploads`
  - idempotent keys (`event_key`, `decision_key`)
  - strict retention bundle contract
- Priority-B has been partially started:
  - profile-aware `validation_runner all`
  - DB-first lineage lookup in analytics collector with local fallback

## Your immediate goals
1. Finish remaining Priority-B items:
   - add `policy_version` to learning gate contract + persistence
   - add regression checks for profile-aware validation expectations
2. Verify distributed-safety assumptions:
   - ensure DB-first lineage query failure handling is deterministic
   - ensure fallback path is clearly logged and measurable
3. Keep backward compatibility:
   - do not break legacy scene/script/shorts outputs
   - keep shadow layers non-blocking and flag-driven

## Execution constraints
- Prefer deterministic contracts over implicit behavior.
- If schema changes, update:
  - `spec/schemas/*.schema.json`
  - `spec/samples/*.json`
  - `spec/SCHEMAS.md`
  - migration SQL if DB columns/indexes changed
- Run and report:
  - `python -m compileall lib spec`
  - relevant `python -m lib.validation_runner ...` commands

## Deliverables expected from you
- code changes + tests/checks
- migration/docs synchronization
- commit + PR message describing risk mitigations
