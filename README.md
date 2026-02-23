# Brand Agency — Multi-Agent Content System

A multi-agent system for DTC brand advertising — from research to production-ready media. Two orchestrated pipelines handle the full lifecycle: **Brand Consulting** researches brands and generates ad concepts, **Media Production** turns those concepts into fal.ai generation scripts and executable media.

Built on the [Claude Agent SDK](https://github.com/anthropics/claude-code-sdk-python) with persistent memory across sessions.

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Brand Consulting Pipeline](#brand-consulting-pipeline)
- [Media Production Pipeline](#media-production-pipeline)
- [Memory System](#memory-system)
- [Project Structure](#project-structure)
- [Output Structure](#output-structure)

Detailed docs:

- [Brand Consulting — Agent Details](docs/brand-consulting.md)
- [Media Production — Agent Details](docs/media-production.md)

## Quick Start

### Prerequisites

- Python 3.12+
- [Anthropic API key](https://console.anthropic.com/)
- [fal.ai API key](https://fal.ai/) (for media generation only)

### Setup

```bash
git clone <repo-url>
cd brand-agency

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install        # Claude Agent SDK CLI dependency
```

Create a `.env` file:

```
ANTHROPIC_API_KEY=sk-ant-...
FAL_KEY=...        # only needed for media generation
```

### Run

```bash
# Pipeline 1: Research brand + generate ad concepts
python main.py

# Pipeline 2: Produce media from ad concepts
python media_production.py
```

## Architecture Overview

```
                        ┌─────────────────────────────────────────┐
                        │         Brand Consulting                 │
                        │           (main.py)                      │
                        │                                         │
  Brand URL ──────────► │  brand_consultant (orchestrator)         │
  Campaign intent        │    ├── brand_researcher                 │
                        │    ├── brand_ad_analyzer                 │
                        │    ├── competitor_paid_analyzer (×N)     │
                        │    ├── competitor_organic_analyzer (×N)  │
                        │    ├── competitive_synthesis             │
                        │    ├── concept_strategist                │
                        │    ├── concept_creator (×5)              │
                        │    └── ad_concept_generator (assembler)  │
                        └──────────────┬──────────────────────────┘
                                       │
                        memory/brands/{slug}/ad_concepts/*/concept.json
                        memory/brands/{slug}/brand.json
                                       │
                        ┌──────────────▼──────────────────────────┐
                        │        Media Production                  │
                        │      (media_production.py)               │
                        │                                         │
  Brand + Concept ────► │  media_consultant (orchestrator)         │
  Products + Context     │    ├── production_director              │
                        │    ├── script_writer                    │
                        │    └── script_runner                    │
                        └──────────────┬──────────────────────────┘
                                       │
                        memory/brands/{slug}/ad_concepts/{concept}/
                          ├── video/*.json  |  image/*.json
                          ├── media_creation_scripts/*.py
                          └── outputs/
```

Both pipelines share the **memory system** (`memory/`) — brand profiles, competitor analysis, and category insights persist across sessions so returning brands skip redundant research.

## Brand Consulting Pipeline

**Entry point:** `python main.py`

Researches a DTC brand, audits its advertising, analyzes competitors (paid + organic split), synthesizes competitive intelligence, and generates ad concepts via a strategist → creator swarm → assembler pipeline.

### Flow

```
Brand URL + Campaign intent
    │
    ▼
[Step 0: Memory Assessment] ── Decide what to reuse vs. re-research (autonomous)
    │
    ▼
[Step 1: Brand Research] ── Identity, products, competitors
    │
    ▼
[Step 2: Parallel Analysis] ── Brand ad audit + (paid + organic) per competitor
    │
    ▼
[Step 2.5: Competitive Synthesis] ── Cross-competitor patterns, whitespace, personas
    │
    ▼
[Step 3a: Concept Strategy] ── 5 content type briefs (memory-aware, avoids duplicates)
    │
    ▼
[Step 3b: Concept Creation ×5] ── 2 concepts per brief = 10 concepts (parallel)
    │
    ▼
[Step 3c: Assembly + QC] ── Brand alignment, overlap check, write concept.json files
    │
    ▼
[Step 4: Present] ── Show concepts, point to media_production.py
```

### Agents (8)

| Agent | Role |
|---|---|
| `brand_consultant` | Orchestrator — manages workflow, memory decisions, agent delegation |
| `brand_researcher` | Researches brand identity, scrapes product catalogue (~10 products), finds 5 competitors |
| `brand_ad_analyzer` | Audits the brand's own ads from Meta Ad Library and social media |
| `competitor_paid_analyzer` | Analyzes a single competitor's PAID advertising (called once per competitor) |
| `competitor_organic_analyzer` | Analyzes a single competitor's ORGANIC/EARNED content (called once per competitor) |
| `competitive_synthesis` | Cross-competitor synthesis — patterns, whitespace, persona mapping, freshness assessment |
| `concept_strategist` | Plans 5 distinct content type briefs, memory-aware (avoids duplicating existing concepts) |
| `concept_creator` | Generates 2 deep ad concepts for one brief (called 5× in parallel) |
| `ad_concept_generator` | Assembler/QC — receives creator outputs, checks alignment and overlap, writes concept.json files |

### Memory-Aware Research

The consultant makes all reuse decisions **autonomously** based on timestamps:

| Data | Fresh (< 14 days) | Aging (14-30 days) | Stale (> 30 days) |
|---|---|---|---|
| Brand profile | Reuse | Reuse | Reuse (identity doesn't change) |
| Ad audit | Reuse | Spot-check | Full re-research |
| Competitor analysis | Reuse | Spot-check | Full re-research |

Campaign intent also influences the decision — a different campaign angle may trigger re-research even if data is fresh.

**Returning brand fast path**: When brand + category memory exist, Steps 1+2 merge into one parallel wave (all agents launch simultaneously).

**All-fresh path**: When everything is < 14 days old, skip research entirely → competitive synthesis → concept generation.

### Output

Individual concept files at `memory/brands/{brand_slug}/ad_concepts/{concept_slug}/concept.json`, each containing a `StoredAdConcept` with content type metadata and a full `AdConcept` (title, format, 5-7 scene storyboard, copy, CTA, product placement notes, talent direction).

See [docs/brand-consulting.md](docs/brand-consulting.md) for agent details and Pydantic schemas.

## Media Production Pipeline

**Entry point:** `python media_production.py`

Takes a pre-selected concept from the brand's concept library and produces structured JSON production guides, fal.ai generation scripts, and executable media.

### Flow

```
Select brand → Campaign context → Select products → Select concept
    │
    ▼
[Step 1] Read concept, summarize, asset inventory
    │
    ▼
[Step 2] production_director — 5 variation .json files (video, image, or both)
    │
    ▼
[Steps 3-5] Select media type → variation → generation model
    │
    ▼
[Step 6] Entity analysis, reference assignment, script_writer
    │
    ▼
[Step 7] Review & modify prompts, execute script
    │
    ▼
[Step 8] Feedback loop (modify prompts, regenerate scenes, or generate another)
```

### Interactive CLI Steps

1. **Select brand** — from memory (with scraped product catalogue)
2. **Campaign context** — describe campaign intent or additional notes
3. **Select products** — choose products from brand catalogue to feature
4. **Select concept** — pick a concept from `ad_concepts/*/concept.json`
5. **Asset inputs** — optional product asset directory and character reference directory
6. **Production guides** — 5 uniquely named `.json` variations generated (if not already present)
7. **Variation + model selection** — pick a creative approach and generation model
8. **Entity analysis** — identifies characters and products across scenes, assigns reference images
9. **Review & execute** — review/modify scene prompts in the generated script, then execute via script_runner
10. **Feedback loop** — modify prompts, regenerate scenes, or generate another script

### Agents

| Agent | Role |
|---|---|
| `media_consultant` | Orchestrator — interactive workflow, entity analysis, agent delegation |
| `production_director` | Generates 5 production guide `.json` files per concept (video, image, or both). Generates negative prompts and post-production notes per variation. |
| `script_writer` | Writes self-contained Python scripts from structured JSON guides with entity-aware prompt adaptation |
| `script_runner` | Executes generation scripts, downloads outputs, stitches video clips, handles regeneration |

### Supported Models

**Video:** veo3.1, veo3 (Google), kling2.0, kling2.1, seedance (ByteDance)
**Image:** flux-pro, flux-dev, sdxl

See [docs/media-production.md](docs/media-production.md) for agent details, structured guide schemas, entity mapping, and script generation.

## Memory System

Persistent memory eliminates redundant research across sessions. All memory is stored as Pydantic-validated JSON in `memory/`.

### Layout

```
memory/
├── brands/{brand_slug}/
│   ├── brand.json          # BrandMemory — profile, visual identity, product catalogue
│   ├── ad_audit.json       # BrandAdAuditMemory — ad formats, gaps, historical tracking
│   └── ad_concepts/
│       └── {concept_slug}/
│           └── concept.json  # StoredAdConcept — content type + full ad concept
│
└── categories/{category_slug}/
    ├── category.json        # CategoryMemory — trending formats, viral patterns, buyer personas, competitive synthesis
    └── competitors/
        └── {slug}.json      # CompetitorMemoryEntry — paid + organic analysis per competitor
```

### What Gets Persisted

**Brand memory** (private per brand):
- Brand profile (name, vibe, category, tone, USP, materials, price range)
- Visual identity (colors, typography, photography style, lighting, aesthetic)
- Product catalogue (~10 products with name, price, description, image URI, features)
- Ad audit (formats, visual style, hooks, strategy gaps)
- Ad concepts (individual concept.json files with storyboards, copy, CTAs)

**Category memory** (shared across brands in same category):
- Competitor analyses (paid ad types, organic formats, visual style, hooks, UGC strategy, spend signals)
- Trending ad formats across the category
- Viral ad patterns (high-performing format combinations)
- Buyer personas (psychographic clusters with purchase drivers)
- Competitive synthesis (cross-competitor patterns, whitespace, persona mapping)

## Project Structure

```
brand-agency/
├── main.py                              # Brand consulting CLI entry point
├── media_production.py                   # Media production CLI entry point
├── models.py                             # Pydantic models (brand, ads, memory, production guides)
├── memory.py                             # Memory utilities (load/save/list)
├── requirements.txt
├── .env                                  # API keys (not committed)
├── CLAUDE.md                             # Project rules for Claude Code
│
├── agents/
│   ├── brand_consulting/
│   │   ├── brand_consultant.py           # Orchestrator prompt + 8-agent registry
│   │   ├── brand_researcher.py
│   │   ├── brand_ad_analyzer.py
│   │   ├── competitor_paid_analyzer.py
│   │   ├── competitor_organic_analyzer.py
│   │   ├── competitive_synthesis.py
│   │   ├── concept_strategist.py
│   │   ├── concept_creator.py
│   │   └── ad_concept_generator.py       # Assembler/QC
│   └── media_production/
│       ├── media_consultant.py           # Orchestrator prompt + agent registry
│       ├── production_director.py
│       ├── script_writer.py
│       └── script_runner.py
│
├── memory/                               # Persistent memory (git-ignored)
│   ├── brands/{brand_slug}/
│   └── categories/{category_slug}/
│
└── docs/
    ├── brand-consulting.md
    └── media-production.md
```

## Output Structure

```
memory/brands/{brand_slug}/ad_concepts/
└── {concept_slug}/
    ├── concept.json                            # StoredAdConcept
    ├── video/
    │   ├── golden_hour_cinematic.json          # VideoProductionGuide
    │   ├── intimate_handheld_closeup.json
    │   └── ...
    ├── image/
    │   ├── minimal_overhead_flat_lay.json      # ImageProductionGuide
    │   └── ...
    ├── media_creation_scripts/
    │   ├── generate_golden_hour_cinematic.py   # fal.ai generation script
    │   └── ...
    └── outputs/
        └── golden_hour_cinematic_veo3_20260222_150000/
            ├── scene_01_establishing_shot.mp4
            ├── scene_02_product_reveal.mp4
            └── golden_hour_cinematic_final.mp4
```

Production guide `.json` files contain structured data (scene-by-scene shot types, lighting, color grading, camera movement, negative prompts, post-production notes) conforming to `VideoProductionGuide` or `ImageProductionGuide` Pydantic schemas — model-agnostic, works with any AI video/image generation tool.
