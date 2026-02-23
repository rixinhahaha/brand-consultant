# Brand Consulting Pipeline — Agent Details

Detailed documentation for the brand consulting pipeline (`main.py`).

## Pipeline Flow

```
Brand URL + Campaign intent
    │
    ▼
brand_consultant (orchestrator)
    │
    ├── [Step 0] Memory Assessment
    │     Autonomously decides what to reuse vs. re-research
    │
    ├── [Step 1] brand_researcher
    │     Brand identity, product catalogue, 5 competitors
    │     Writes → memory/brands/{slug}/brand.json
    │
    ├── [Step 2] Parallel:
    │     ├── brand_ad_analyzer (if audit needs refresh, returns text)
    │     │     memory_writer → memory/brands/{slug}/ad_audit.json
    │     ├── Per competitor (only stale/new):
    │     │     ├── competitor_paid_analyzer (returns text)
    │     │     └── competitor_organic_analyzer (returns text)
    │     │     memory_writer → memory/categories/{slug}/competitors/{slug}.json
    │     └── Brand itself (same paid+organic analyzers):
    │           memory_writer → memory/categories/{slug}/competitors/{brand_slug}.json
    │
    ├── [Step 2.5] competitive_synthesis
    │     Reads competitor JSON files (including the brand itself), identifies patterns + whitespace
    │     memory_writer → memory/categories/{slug}/category.json
    │
    ├── [Step 3a] concept_strategist
    │     Plans 5 content type briefs (memory-aware, avoids duplicates)
    │
    ├── [Step 3b] concept_creator × 5 (parallel)
    │     2 concepts per brief = 10 concepts total
    │
    ├── [Step 3c] ad_concept_generator (assembler/QC)
    │     Brand alignment + overlap check, returns validated concepts
    │     memory_writer × 10 → memory/brands/{slug}/ad_concepts/{concept_slug}/concept.json
    │
    └── [Step 4] Present concepts
          Point to `python media_production.py`
```

## Agent Details

### brand_consultant (Orchestrator)

The main orchestrator. Receives the user's brand URL and campaign intent, then manages the full workflow.

**Key responsibilities:**
- Assess memory freshness and decide what to reuse
- Delegate to specialist agents via the Task tool
- Merge paid + organic competitor results and delegate to **memory_writer** for persistence
- Coordinate the strategist → creator swarm → assembler pipeline
- Present final concepts to the user
- Handle multi-turn feedback (re-generate concepts with modifications)

**Tools:** Task (delegation), Read, Glob, Write, WebSearch, WebFetch

**Memory decisions are autonomous** — the consultant briefly tells the user the plan ("Reusing brand profile from 3 days ago, refreshing 2 stale competitors") then proceeds without waiting for confirmation.

**Fast paths:**
- **Returning brand**: Steps 1+2 merge into one parallel wave (brand_researcher + brand_ad_analyzer + all competitor agents launch simultaneously)
- **All-fresh**: Skip research entirely → competitive synthesis → concept generation

### brand_researcher

Researches a brand from scratch or updates an existing profile.

**What it produces:**
- `BrandProfile` — name, vibe (3-5 adjectives), category, price range, materials, tone, USP
- 5 competitors with Instagram handles
- Product catalogue (~10 products with name, price, description, image URI, key features)
- Visual identity (colors, typography, photography style, lighting, aesthetic)

**Memory-aware mode:**
- If existing `brand.json` provided → validate with 1-2 quick searches, update only what changed
- If products list is empty → scrape the catalogue
- Always update competitors (landscape shifts frequently)

**Tools:** WebSearch, WebFetch, Read, Write

### brand_ad_analyzer

Audits the brand's own advertising creative. Returns text to the orchestrator (does not write files — the orchestrator delegates to **memory_writer**).

**What it produces:**
- Ad formats the brand uses (type, description, platform source)
- Visual style (color palette, lighting, editing)
- Hooks (2-3 common opening patterns)
- Strategy gaps (2-3 missed opportunities)

**Memory-aware mode:**
- If audit is recent (< 14 days) → skip entirely
- If aging → spot-check update
- If stale → full audit
- Tracks gap progress against prior findings (`historical_gaps`)

**Tools:** WebSearch, WebFetch, Read

### competitor_paid_analyzer

Analyzes a single competitor's **paid** advertising. Called once per competitor and once for the brand itself (the brand is included in category competitors for symmetric synthesis).

**What it produces:**
- 2-4 paid ad formats (type, description, why it works)
- Visual style of paid creative
- Hooks (first-3-second patterns)
- CTAs
- Creative testing patterns (A/B testing observations)
- Spend signals (active ads count, run duration, geographic targeting)
- Trending paid formats in the category

**Returns text** to the orchestrator — does not write files. The orchestrator merges paid + organic results and writes the combined entry to memory.

**Tools:** WebSearch, WebFetch

### competitor_organic_analyzer

Analyzes a single competitor's **organic/earned** content. Called once per competitor (and the brand itself), in parallel with the paid analyzer.

**What it produces:**
- 3-5 organic content formats (behind-the-scenes, UGC reposts, styling flat lays, etc.)
- Content themes and engagement patterns
- Content cadence (posting frequency, platform distribution, content mix ratio)
- UGC/creator strategy (creator tiers, brand guidelines, incentives)
- Community engagement (comment response, interactive content, sentiment)

**Returns text** to the orchestrator — does not write files.

**Tools:** WebSearch, WebFetch

### competitive_synthesis

Cross-competitor analysis with freshness assessment. Called after all competitor data is written to memory.

**What it produces:**
- **Freshness assessment**: Categorizes each competitor as fresh (< 14 days), aging (14-30), or stale (> 30) based on `last_researched` date
- **Category patterns** (3+ competitors do this): common formats, styles, hooks, cadence
- **Whitespace opportunities** (no competitor does this): untapped formats, themes, audiences, platforms
- **Differentiators** (1-2 competitors only): unique approaches, emerging trends
- **Persona mapping**: over-served vs under-served segments
- **Campaign-specific recommendations**: top insights, differentiation angles

**Tools:** Read, Glob (no web access)

### concept_strategist

Plans 5 distinct content type briefs. Memory-aware — reads existing concepts to avoid duplicates.

**What it produces per brief:**
- Content type name + strategic rationale
- Format direction (Reel, Carousel, Static, etc.)
- Target persona (from category memory)
- Key competitive insight (what inspired this brief)
- Differentiation angle
- Tone and mood
- Product focus + constraints
- Existing concept gap (what gap this fills in the library)

**Quality checks:**
- All 5 briefs genuinely distinct (different formats, personas, angles)
- None duplicate existing concepts in memory
- Each references specific competitive evidence
- Format diversity across the 5 briefs

**Tools:** Read, Glob

### concept_creator

Generates 2 deep ad concepts for ONE content type brief. Called 5× in parallel (once per brief from the strategist).

**What it produces per concept:**
- Title + format
- Storyboard (5-7 scenes with specific visual, audio/text, duration)
- Ad copy + CTA
- Competitor reference
- Product placement notes
- Talent direction
- Post-production guidance (creative intent level — e.g., "rhythmic editing synced to beat drops")

Does NOT generate negative prompts — those are produced by the production_director per variation.

**Tools:** none (returns text to orchestrator)

### ad_concept_generator (Assembler/QC)

Receives 5 concept_creator outputs (10 concepts total). Performs quality control and returns validated concept JSON objects. Does not write files — the orchestrator delegates to **memory_writer** for persistence.

**QC checks:**
- Brand alignment (tone, product placement, CTA)
- Overlap between new concepts
- Overlap with existing concept library
- Storyboard quality (5-7 scenes, specific descriptions, narrative flow)

**Returns:** 10 `StoredAdConcept` JSON objects — content_type, content_type_hook, why_it_works, campaign_intent, created_date, hashtags, concept (AdConcept). The orchestrator persists each to `memory/brands/{brand_slug}/ad_concepts/{concept_slug}/concept.json` via memory_writer.

**Tools:** Read, Glob

### memory_writer

Takes raw or structured data from any agent and writes schema-compliant JSON to the memory directory. Schemas are auto-generated from the Pydantic models in `models.py` at import time, so they stay in sync automatically.

**Supports:** `BrandMemory`, `BrandAdAuditMemory`, `CompetitorMemoryEntry`, `CategoryMemoryFile`, `StoredAdConcept`

> **Note:** `category.json` stores `competitor_slugs` (not full competitor objects). Individual `competitors/{slug}.json` files are the source of truth. `load_category_memory()` assembles the full `CategoryMemory` by loading each competitor file.

**Called by:** the orchestrator after receiving results from brand_ad_analyzer, competitor analyzers, or competitive_synthesis.

**Tools:** Write, Read

## Pydantic Models

The consulting pipeline uses these core models (defined in `models.py`):

### Brand Research

| Model | Fields |
|---|---|
| `BrandProfile` | name, instagram, vibe, category, price_range, materials, tone, usp |

### Ad Analysis

| Model | Fields |
|---|---|
| `BrandAdFormat` | type, description, platform |
| `BrandAdAnalysis` | ad_formats, visual_style, hooks, strategy_gaps |
| `AdType` | type, description, why_it_works |
| `TrendingFormat` | format, description, which_brands |

### Ad Concepts

| Model | Fields |
|---|---|
| `StoryboardScene` | scene, visual, audio_or_text, duration_seconds |
| `AdConcept` | title, format, storyboard, copy, cta, reference, product_placement_notes, talent_direction |
| `StoredAdConcept` | content_type, content_type_hook, why_it_works, campaign_intent, created_date, hashtags, concept (AdConcept) |

### Memory Models

| Model | Fields |
|---|---|
| `VisualIdentity` | primary_colors, color_palette, typography_style, photography_style, lighting_preference, overall_aesthetic |
| `ProductEntry` | name, description, price, image_uri, key_features |
| `BrandMemory` | brand, category_slug, last_updated, visual_identity, products |
| `BrandAdAuditMemory` | brand_slug, last_updated, ad_audit, historical_gaps |
| `CompetitorMemoryEntry` | name, slug, instagram, why, ad_types, visual_style, hooks, organic_content_formats, content_cadence, ugc_creator_strategy, creative_testing_patterns, spend_signals, buyer_personas_targeted, viral_patterns, last_researched |
| `BuyerPersona` | label, description, age_range, psychographics, purchase_drivers, brands_targeting |
| `ViralAdPattern` | pattern_name, description, why_it_works, example_brands, estimated_engagement |
| `CategoryMemory` | category, category_slug, last_updated, competitors, trending_formats, viral_ad_patterns, buyer_personas, competitive_synthesis |
| `CategoryMemoryFile` | category, category_slug, last_updated, competitor_slugs, trending_formats, viral_ad_patterns, buyer_personas, competitive_synthesis |

## Feedback Loop

After presenting concepts, users can provide feedback through the conversational CLI:

1. The consultant determines which step(s) need to re-run based on the feedback
2. Re-delegates to the appropriate agent(s), incorporating the feedback plus all prior findings
3. If feedback affects strategy → re-run concept_strategist → concept_creators → assembler
4. If feedback is about specific concepts → re-run individual concept_creators with adjusted briefs
5. New concepts are written as additional files in the ad_concepts directory (never overwrite existing)
6. Presents updated concepts

Type `exit` or `quit` to end the session.
