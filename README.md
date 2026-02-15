# AI-Native Finance Content System

## Overview
This repository defines an AI-native, agent-based content production system
for high-CPM finance & economics YouTube channels.

The system is designed to:
- Maximize retention and monetization
- Minimize manual work
- Enable multi-channel scaling
- Enforce spec-driven execution

This is not a prompt collection.
This is an operating system for an AI-driven media company.

## Core Principles
- Profit-first
- Automation-first
- Spec-driven agents
- Continuous evaluation and rewrite loops

## Repository Structure
/spec
  PRD.md
  PRODUCT_SPEC.md
  RULES.md
  SYSTEM_ARCH.md
  MULTI_SKILL_MODE.md
  schemas/
  samples/
  AGENTS.md
  AGENT_RULES.md
  STYLE.md
  EVAL.md
  ROADMAP.md
  MAIN_CONTEXT.md
  TECH_SPEC.md

/prompts
  system.md
  planner.md
  research.md
  evaluator.md

/mcp
  mcp_config.md

## Execution Model (Current Runtime)
Hook Shadow (optional, non-blocking)
 → Research
 → Plan
 → Script (long + shorts)
 → Beat Shadow (optional)
 → Visual Beat Shadow (optional)
 → Shorts Intelligence Shadow (optional)
 → Scene Assembly (legacy envelope preserved)
 → Metadata
 → Validate
 → Retention Events Shadow (optional)
 → Analytics Collector (outcome snapshots)
 → Learning Gate

## CLI Usage (Current)
```bash
python -m lib.trend_scout
python -m lib.researcher
python -m lib.planner
python -m lib.scripter
python -m lib.metadata_generator data/<video_id>_plan.json data/<video_id>_script.json
python -m lib.validation_runner all --url <youtube_url_or_id>
python -m lib.pipeline_runner --url <youtube_url_or_id> --validate
python -m lib.analytics_collector <video_id> [start_date] [end_date]
python -m lib.analytics_collector path/to/video_ids.txt [start_date] [end_date]

# Optional shadow flags
# HOOK_SHADOW_ENABLED=true
# BEAT_SHADOW_ENABLED=true
# VISUAL_BEAT_SHADOW_ENABLED=true
# SHORTS_INTEL_SHADOW_ENABLED=true
# RETENTION_EVENTS_ENABLED=true
```

### Environment Setup
- Copy `.env.example` to `.env` and populate API keys.
- Each stage writes local backups to `data/<stage>_<video_id>.json`.
- Outputs are upserted to Supabase to avoid duplicate rows on refresh.

## Golden Rule
Spec files override all agent instructions.
All agents must load spec context before execution.
