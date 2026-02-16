# Complete System Understanding (Repository-Wide)

## Scope and Method
This document was produced after a full repository read, including:
- runtime code under `lib/` and root scripts,
- product/specification documents under `spec/` and `docs/`,
- prompt contracts under `prompts/`,
- schemas under `spec/schemas/`, `spec/schema.sql`, and `sql/2026-02-15_shadow_learning_schema.sql`,
- runtime artifacts in `data/` and configuration in `config/`.

The goal is to capture **actual inferred architecture from code**, not intended architecture from prose alone.

---

## 1) System Purpose (Inferred)
The repository implements an AI-native YouTube content factory for finance/economics channels that optimizes for:
- retention,
- monetization packaging,
- reproducible stage outputs,
- and gradual self-improvement via analytics feedback.

The implemented control plane is a **single-process orchestrator** (`lib/pipeline_runner.py`) that executes stage modules, persists artifacts locally and to Supabase, and conditionally enables shadow-learning layers.

---

## 2) Runtime Architecture (Code-Inferred)

### 2.1 Control Plane Pattern
- **Orchestrator-centric execution**: `run_pipeline()` is the primary controller.
- **Stage-level retries** via `_run_stage()` with transient error detection and exponential backoff.
- **Checkpointing strategy** via local `data/<video_id>_<stage>.json` files and DB upserts.
- **Manifest pattern** via `data/<video_id>_pipeline.json` to record profile/toggles + artifact paths.

### 2.2 Stage Graph (Observed)
The effective pipeline graph is:
1. optional hook seed shadow,
2. research,
3. plan,
4. long + shorts script generation,
5. optional hook refined shadow,
6. optional beat shadow,
7. optional visual beat shadow,
8. optional shorts intelligence shadow,
9. scene generation (legacy scene contract wrapper),
10. metadata generation,
11. validator + optional script repair loop,
12. optional retention feature snapshot,
13. optional upload path,
14. optional analytics collector / learning gate outside the primary run.

### 2.3 Data Plane Pattern
Dual persistence:
- **Local artifact store** (`data/`) for replay and auditability,
- **Supabase operational tables** for reuse, upsert/idempotency, and downstream learning.

This is a practical hybrid architecture: local durability first, cloud consistency second.

---

## 3) Storage and Schema Model

### 3.1 Core Tables
Core schema (`spec/schema.sql`) supports:
- content memory (`research_cache`, `planning_cache`, `scripts`),
- publish assets (`video_scenes`, `video_metadata`, `video_scripts`, `video_uploads`),
- experiment telemetry (`metadata_experiments`).

### 3.2 Shadow/Learning Expansion
Migration (`sql/2026-02-15_shadow_learning_schema.sql`) adds:
- `retention_events` (feature and outcome snapshots + idempotent event keys),
- `learning_gates` (latest policy decision snapshot),
- `learning_gate_decisions` (append-only decision history).

### 3.3 Contract Governance
JSON schemas in `spec/schemas/` formalize structured outputs for:
- research/plan/script/scene,
- hook/beat/visual beat/shorts intelligence,
- retention events and learning gate.

This is contract-first by design, even though enforcement is selective in runtime paths.

---

## 4) Implicit Architecture Patterns (Detected)

1. **Local-first resilience with DB fallback/upsert**
   - many paths tolerate DB issues by keeping local artifacts.

2. **Shadow-layer feature flagging**
   - optional quality/intelligence layers are non-blocking.

3. **Soft-fail learning loop**
   - learning signals are generated opportunistically; core content path still proceeds.

4. **Spec-as-governance duality**
   - detailed governance docs exist, but runtime enforcement varies by stage.

5. **Schema migration in-flight architecture**
   - code indicates transition from baseline pipeline toward enterprise-grade evaluative loop.

---

## 5) Architectural Risks and Failure Modes

### 5.1 Profile Resolution Ambiguity in Orchestrator
`lib/pipeline_runner.py` defines `resolve_pipeline_profile()` twice with different signatures/behavior. This introduces maintainability risk and potential misread of profile semantics during refactors.

### 5.2 Monolithic Orchestrator Complexity
`pipeline_runner.py` has very high responsibility density (stage orchestration, schema recovery, scene synthesis logic, retry policy, logging, upload path). This increases coupling and regression surface.

### 5.3 Weak Deterministic Guarantees for LLM Outputs
There is strong post-hoc repair/validation logic, but deterministic generation contracts are still mostly prompt-constrained. At higher scale this can produce brittle edge-case outputs and costly reruns.

### 5.4 Partial Exactly-Once Semantics
Some idempotency exists (event keys, upserts), but not all stages are protected by consistent run-scoped idempotency keys. Retries can still duplicate expensive external calls.

### 5.5 Missing Queue/Worker Isolation
The current model is single-process synchronous orchestration. At 10x+ throughput, failures in one long run can block capacity and create noisy-neighbor effects.

### 5.6 Observability Fragmentation
Run logs exist, but there is no strongly defined SLO dashboard contract in code and no explicit tracing context propagated across all side effects.

---

## 6) Scalability View (10× / 100×)

### At 10× workload
- contention around single orchestrator process,
- harder recovery for partial stage failures,
- rising cost from retries + regeneration,
- uneven quality due to model variability.

### At 100× workload
- need for distributed job orchestration,
- need for strict idempotency and dedupe at stage boundary,
- queue-based backpressure and concurrency controls become mandatory,
- artifact/version lineage must become first-class (not just local files).

---

## 7) System-Level Improvements (Proactive)

### This was not asked, but is important because...
without these layers, long-term reliability and scale economics will degrade faster than content quality improves.

1. **Introduce Stage Execution Ledger (required)**
   - Why needed: exact run/stage state machine with idempotency keys.
   - Prevents: duplicate work, inconsistent retries, hard-to-debug partial completion.
   - What breaks if omitted: nondeterministic replay and cost blowups under retry storms.

2. **Split Orchestrator into Explicit Stage Workers**
   - Why needed: isolate failures and enable horizontal scaling.
   - Prevents: one stage’s latency/error from collapsing full pipeline throughput.
   - What breaks if omitted: capacity ceiling and operational fragility at multi-channel scale.

3. **Promote Contracts to Hard Runtime Gates for Every Stage**
   - Why needed: prevent malformed artifacts from moving downstream.
   - Prevents: cascading silent corruption into metadata/learning systems.
   - What breaks if omitted: low-trust analytics and contaminated feedback loops.

4. **Define Determinism Envelope for Model Calls**
   - Why needed: bounded variability by stage (temperature/model/repair budget).
   - Prevents: run-to-run semantic drift that defeats learning comparisons.
   - What breaks if omitted: invalid A/B inference and unstable policy updates.

5. **Add Queue + Dead-Letter + Retry Budget Policy**
   - Why needed: production-safe failure handling under external API instability.
   - Prevents: infinite retries and hidden starvation.
   - What breaks if omitted: backlog growth and unpredictable SLA misses.

6. **Create End-to-End Telemetry Contract**
   - Why needed: consistent metrics/traces across generation, validation, upload, and analytics.
   - Prevents: blind spots in quality/cost/latency diagnostics.
   - What breaks if omitted: inability to tune system-level bottlenecks reliably.

---

## 8) Current Maturity Assessment
- **Strengths**: rich specs, schema assets, practical retries, hybrid persistence, shadow-learning scaffolding.
- **Weaknesses**: orchestrator monolith, partial determinism, uneven contract enforcement.
- **Readiness**:
  - Single-channel / low concurrency: workable.
  - Multi-channel / enterprise scale: requires control-plane decomposition + stronger execution contracts.

---

## 9) Recommended Next Milestones (High-Impact Order)
1. Remove duplicate profile resolution function and centralize toggle policy.
2. Extract `pipeline_runner.py` into stage adapters + orchestrator core.
3. Add stage execution ledger table with unique `(video_id, run_id, stage, attempt)` constraints.
4. Enforce schema validation pre- and post-persistence for all generated artifacts.
5. Add queue-backed execution mode with dead-letter handling.
6. Build KPI/SLO dashboards keyed by run/stage identifiers.

---

## 10) Final Inference
The repository is beyond a prototype: it is a **transitional production system** with strong design intent and meaningful runtime safeguards. The key gap is not feature breadth; it is **control-plane hardening** for deterministic, scalable, and auditable multi-channel operation.
