# /spec/Pipeline_Refactor_Spec v2.md

🎯 Goal

Upgrade pipeline from:

Research → Plan → Script → Scene → Meta → Validate


To retention-optimized production pipeline.

1️⃣ HOOK FIRST ARCHITECTURE
Purpose

Define attention vector BEFORE data collection.

Why

Traditional:
Research → Info → Script → Weak Hook

Optimized:
Hook Hypothesis → Research to Support Hook

Implementation

Add new stage BEFORE research:

Hook Generation
Hook Validation (Trend / CTR Prediction)
Hook Confidence Score

Hook Data Model
{
  "hook_text": "",
  "curiosity_gap_score": 0-1,
  "emotional_trigger": [],
  "power_keywords": [],
  "retention_prediction": 0-1
}

2️⃣ SCENE → BEAT SYSTEM (CORE CHANGE)
OLD

Scene = Information Block

NEW
Beat = Narrative Unit

Story progression unit.

Visual Beat = Visual Change Unit

Screen change / attention reset unit.

Target Ratios
1 Beat = 1~3 Visual Beats

Beat Example
Beat: Financial power expansion
Visual Beat 1: Map expansion
Visual Beat 2: Bank interior
Visual Beat 3: Document signing

3️⃣ SCENE ASSEMBLY MODEL

Scene becomes OUTPUT artifact, not planning unit.

Scene Structure
{
  "beat_id": "",
  "visual_beats": [],
  "voiceover_text": "",
  "image_prompt": "",
  "motion_prompt": ""
}

4️⃣ NARRATIVE DENSITY CONTROL (NEW)

Controls scene count automatically.

Density Modes
LOW → Documentary
MEDIUM → Standard YouTube
HIGH → Viral Automation Style

Viral Target
5 min video:
18~28 Visual Beats

5️⃣ RETENTION CURVE PLANNING (NEW)
Required Structure
0~5 sec

Curiosity Shock

5~20 sec

Proof Signal

20~60 sec

Story Anchor

6️⃣ VISUAL RHYTHM RULES
Hard Constraints

Max static visual time:

3 seconds

Motion Types
Micro motion
Camera motion
Object motion
Light motion

7️⃣ IMAGE / MOTION SPLIT STRATEGY
Generation Phase

Combine (Speed)

Storage Phase

Separate (Flexibility)

Recommended DB Structure
Scene Table
Beat Table
Visual Beat Table
Asset Table

8️⃣ THUMBNAIL LEARNING LOOP
New Feedback Layer
Thumbnail Pattern Extraction
Hook Correlation Tracking
CTR Training Dataset

9️⃣ VALIDATION UPGRADE
Old Validation

Logic / Fact only

New Validation
Retention Risk
Visual Stagnation Risk
Hook Drift Score

🔟 FUTURE AUTO-LEARNING PREP

Store:

Hook Type

Beat Density

Visual Change Frequency

CTR

Retention Curve

🎯 PROMPT SPEC FOR AGENTS
Hook Generator Prompt
Generate 5 hook candidates optimized for:
- Curiosity gap
- Financial power theme
- Long timeline influence
- High CTR potential
Avoid conspiracy framing.

Beat Planner Prompt
Expand narrative into beats, not scenes.

Rules:
Each beat = story progression step.
Each beat must create curiosity continuation.
Target: 8~12 beats for 5 min video.

Visual Beat Expander Prompt
Expand each beat into visual beats.

Rules:
Max 3 seconds per visual.
Each visual must introduce new stimulus.

🚀 MIGRATION PLAN
Phase 1

Add Hook Layer only.

Phase 2

Convert Scene → Beat System.

Phase 3

Add Retention Planning.