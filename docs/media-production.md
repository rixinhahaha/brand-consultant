# Media Production Pipeline — Agent Details

Detailed documentation for the media production pipeline (`media_production.py`).

## Pipeline Flow

```
Select brand → Select products → Campaign context → Collect assets
    │
    ▼
media_consultant (orchestrator)
    │
    ├── [Step 1] Concept & product matching
    │     Products selected → recommend concepts (top 3)
    │     No products → present concepts, then auto-pick products
    │
    ├── [Step 2] Read & summarize selected concept
    │     Asset inventory (product images, character refs)
    │
    ├── [Step 3] production_director
    │     Generate 5 variation .json files (video, image, or both)
    │     Writes → memory/brands/{slug}/ad_concepts/{concept}/[video|image]/*.json
    │
    ├── [Steps 4-6] Interactive selection
    │     Media type → Variation → Model
    │
    ├── [Step 7] Entity analysis + reference assignment
    │     script_writer generates fal.ai script
    │     Writes → {concept_dir}/media_creation_scripts/*.py
    │
    ├── [Step 8] Review & execute
    │     Review/modify prompts in generated script, then execute
    │
    └── [Step 9] Feedback loop
          Regenerate, modify prompts, or generate another
          Writes → {concept_dir}/outputs/*/
```

## CLI Flow

The interactive CLI collects inputs before handing off to the agent:

```
1. Select brand (from memory)
2. Select products (from brand's scraped catalogue, or skip)
3. Campaign context (free text)
4. Optional asset inputs (product assets dir, character refs dir)
```

All available concepts are loaded automatically and passed to the consultant. The agent handles concept recommendation and selection interactively (Step 1 of the workflow).

### Product Selection

When the brand has a scraped product catalogue (from the consulting pipeline), users get an interactive product selection step:

```
  Product catalogue (12 products):

    1. Gold Anchor Charm Bangle — $38.00
       Delicate gold-tone bangle with anchor charm, adjustable wire...
    2. Silver Moon Phase Bracelet — $42.00
       Sterling silver bracelet featuring crescent moon phases...
    ...

  Enter product numbers (comma-separated), 'all', or press Enter to skip.
  Select products: 1,3,7
```

Product selection drives concept recommendation:
- **Products selected** — the consultant recommends concepts that best showcase those products (Mode A)
- **No products selected** — the consultant presents all concepts, then auto-picks the most suitable products after the user chooses a concept (Mode B)

## Agent Details

### media_consultant (Orchestrator)

Manages the interactive workflow from concept review through media execution.

**Step 1: Concept & Product Matching**

All concepts and the full product catalogue are provided in the initial prompt. The consultant runs in one of two modes:

| Mode | Trigger | Behavior |
|---|---|---|
| **Mode A** | User pre-selected products | Analyze each concept's `product_placement_notes`, storyboard, and `content_type` to rank the top 3 concepts for those products. Present with reasoning. |
| **Mode B** | No products selected | Present all concepts as a numbered list. After user picks one, analyze the concept to recommend 2-4 products from the catalogue. |

After concept and products are settled, the consultant proceeds to Step 2.

**Step 2: Read & Summarize Concept**

The agent reads the selected concept JSON, summarizes it (title, format, scene count, duration, copy, CTA), and inventories any provided assets.

**Step 3: Production Guide Generation**

If `.json` guide files don't already exist for this concept, delegates to the production_director. The media type is inferred from the concept's format:

| Format | Primary Type | Also Generate |
|---|---|---|
| Reel / Video | Video | Image (if thumbnail/cover frame needed) |
| Story | Depends on storyboard | Video story or static story cards |
| UGC | Video | Image (if photo testimonial or before/after grid) |
| Static | Image | Video (if animated/cinemagraph implied) |
| Carousel | Image | Video (if cards describe motion) |

When in doubt, generates both.

**Step 7: Entity-Aware Analysis**

The most complex step. The consultant:

1. Identifies distinct characters across scenes (groups by description consistency)
2. Identifies distinct products (product-only scenes)
3. Analyzes character consistency (same person across scenes vs. intentionally different)
4. Flags sub-scene edge cases (multiple characters in one generated scene)

Then assigns references via one of two modes:

| Mode | Trigger | Behavior |
|---|---|---|
| **Auto-Match** | Asset directories provided upfront | Views reference images, auto-matches to entities, presents mapping for confirmation |
| **Manual** | No directories provided | Prompts user per entity for reference paths |

**Product reference fallback:**
- Product asset dir + selected products → match directory images to products (higher quality)
- Selected products, no asset dir → offer catalogue image URIs as references
- Product asset dir, no selected products → use directory images

After reference assignment, the consultant views every reference image and writes a `ref_visual_description` — a detailed natural-language description passed to the script writer so it doesn't need to re-analyze the images.

**Tools:** Task (delegation), Read, Glob, Write, Bash

### production_director

Generates 5 uniquely named production guide `.json` files for a single ad concept. Now generates negative prompts and post-production notes per variation (these are no longer carried on the concept).

**Video variations** explore different creative dimensions:
- Camera style (handheld vs gimbal vs static vs drone)
- Lighting (natural vs studio vs golden hour vs neon)
- Pacing (fast-cut montage vs slow-build vs single-take)
- Mood (raw/authentic vs polished/cinematic vs editorial)
- Focus (product-centric vs emotion-centric vs lifestyle)

**Image variations** explore:
- Composition (flat-lay vs lifestyle vs editorial vs macro)
- Lighting (window light vs studio strobe vs dramatic vs soft diffused)
- Styling (minimal vs maximal vs textured vs clean)
- Perspective (overhead vs eye-level vs angled vs worm's eye)

**Output:** Each `.json` file conforms to `VideoProductionGuide` or `ImageProductionGuide` Pydantic schema:

**VideoProductionGuide** fields:
- concept_title, variation_name, variation_slug, format
- total_duration_seconds, scene_count, ad_copy, cta, aspect_ratio
- brand_visual_direction, generation_prompt (single cohesive paste-ready paragraph)
- scenes[] — each with: scene_number, scene_title, duration_seconds, shot_type, camera_angle, camera_movement, framing, key_light, light_quality, light_mood, subject, action, expression, background, depth_of_field, color_palette, color_grade, voiceover, music, text_overlay
- reference_assets, style_references
- negative_prompts (5-7 per variation: brand-specific + AI-artifact + variation-specific)
- post_production_notes (5-8 per variation: transitions, color grading, music, text overlay, sound design)

**ImageProductionGuide** fields:
- Similar structured fields for composition, lighting, color palette, typography
- cards[] for carousel format (CarouselCardGuide per card)
- negative_prompts, post_production_notes (same ownership as video)

**Tools:** Write

### script_writer

Writes self-contained Python scripts that call fal.ai APIs from structured JSON production guide data.

**Input:**
- Full `.json` variation contents (structured data, not markdown)
- Model name (veo3.1, veo3, kling2.0, flux-pro, etc.)
- Media type (video or image)
- Entity mapping (characters + products with labels, scenes, ref paths, visual descriptions)

**Field mapping from JSON:**
- `VideoProductionGuide.scenes[i]` → `SCENES[i]` in the script
- `VideoProductionGuide.negative_prompts` → `NEGATIVE_PROMPTS` (joined with " | ")
- `VideoProductionGuide.brand_visual_direction` → `BRAND_DIRECTION`
- `VideoProductionGuide.generation_prompt` → overall prompt context
- `VideoProductionGuide.aspect_ratio` → `ASPECT_RATIO`

**Entity-aware prompt modes:**
- **Default mode** (no reference): Full scene field combination
- **Character-ref mode**: Removes appearance descriptions, keeps action/expression/movement
- **Product-ref mode**: Removes product names/materials, keeps arrangement/composition

**CLI options in generated script:**
```
--model {model}
--character-ref {paths...}
--product-ref {paths...}
--output-dir {directory}
--resolution {720p|1080p}
--generate-audio          # veo3 only
--skip-stitch
--scenes {scene_numbers}  # regenerate specific scenes
--stitch-only             # re-stitch without regenerating
```

**Tools:** Read, Write

### script_runner

Executes generation scripts, manages outputs, handles regeneration.

**What it does:**
1. Builds execution command with all flags
2. Runs script with 10-minute timeout (fal.ai generation is slow)
3. Verifies output files via Glob
4. Reports structured results (scenes generated, transitions, final video path)

**Tools:** Bash, Read, Glob

## Structured Production Guide Schemas

Production guides use structured JSON instead of markdown. The schemas are defined as Pydantic models in `models.py`:

### VideoProductionGuide

```
VideoProductionGuide
├── concept_title, variation_name, variation_slug
├── format, total_duration_seconds, scene_count
├── ad_copy, cta, aspect_ratio
├── brand_visual_direction
├── generation_prompt
├── scenes: list[SceneProductionGuide]
│   └── scene_number, scene_title, duration_seconds
│       shot_type, camera_angle, camera_movement, framing
│       key_light, light_quality, light_mood
│       subject, action, expression
│       background, depth_of_field
│       color_palette, color_grade
│       voiceover, music, text_overlay
├── reference_assets, style_references
├── negative_prompts: list[str]
└── post_production_notes: list[str]
```

### ImageProductionGuide

```
ImageProductionGuide
├── concept_title, variation_name, variation_slug
├── format ("Static" | "Carousel"), aspect_ratio
├── ad_copy, cta
├── brand_visual_direction, generation_prompt
├── composition, perspective, framing, focal_point
├── primary_subject, positioning, props_styling, scale
├── key_light, fill, color_temperature, light_mood
├── dominant_colors, accent_colors, grade
├── setting, surface_backdrop, depth_of_field
├── text_placement, font_style, text_color
├── cards: list[CarouselCardGuide]  (carousel only)
├── overall_visual_consistency  (carousel only)
├── reference_assets, style_references
├── negative_prompts: list[str]
└── post_production_notes: list[str]
```

## Negative Prompt Ownership

Negative prompts are generated by the **production_director** per variation, NOT carried on the concept. Each variation gets 5-7 negative prompts combining:

1. **Brand-specific** (2-3): Off-brand aesthetics, wrong visual tone
2. **AI-artifact** (2-3): Morphing faces, extra fingers, temporal flickering, distorted text
3. **Variation-specific** (1-2): What would undermine this creative direction

Same treatment for **post_production_notes** — generated fresh per variation by the production_director.

## Entity Mapping Format

The entity mapping connects reference images to storyboard scenes:

```yaml
characters:
  - label: "Character A"
    description: "Woman, late 20s, simple warm-toned clothing"
    scenes: [2, 4]
    ref_provided: true
    ref_index: 0
    ref_path: "/path/to/character_a.jpg"
    ref_visual_description: >
      Woman in her late 20s with warm olive skin, shoulder-length
      dark brown hair, cream linen blouse, calm expression.

products:
  - label: "Product A"
    description: "Gold anchor charm bangle on champagne fabric"
    scenes: [1, 5]
    ref_provided: true
    ref_index: 0
    ref_path: "/path/to/product_a.jpg"
    ref_visual_description: >
      Three delicate gold-tone charm bangles on cream linen,
      anchor/moon/heart charms, warm polished finish.
```

- `ref_index` is sequential (0, 1, 2...) within each category
- `ref_visual_description` is the consultant's pre-analyzed observation from viewing the image
- Entities with `ref_provided: false` get `null` for ref fields

## Feedback Loop

After execution, users choose:

1. **Satisfied** — generate another script or exit
2. **Regenerate specific scenes** — re-run with existing prompts for selected scenes, re-stitch
3. **Regenerate all** — full execution with new output directory
4. **Modify prompts** — review current prompts, apply natural-language changes (e.g. "make scene 2 more dramatic", "change lighting to golden hour"), then re-execute affected scenes or all scenes

Prompt modification uses the same sub-workflow available during initial review (Step 8): read the script, show prompt text, accept changes, write the updated script, show a diff summary. Users can also modify global constants (NEGATIVE_PROMPTS, BRAND_DIRECTION, durations, aspect ratio).

The loop continues until the user exits.
