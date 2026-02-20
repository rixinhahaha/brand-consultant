# Ad Content Generator — Multi-Agent System

A multi-agent system that researches a DTC brand, audits its advertising, analyzes competitors, generates ad concepts with full storyboards, and produces model-agnostic AI production prompts — all orchestrated through a conversational CLI.

## Architecture

A **Brand Consultant** orchestrator delegates to 6 specialist agents:

| Agent | Role |
|---|---|
| `brand_researcher` | Researches brand identity, products, audience, and 5 competitors |
| `brand_ad_analyzer` | Audits the brand's own ads from Meta Ad Library and social media |
| `competitor_ad_analyzer` | Analyzes a single competitor's ad creative (called once per competitor) |
| `ad_concept_generator` | Generates 5 content types x 2 ads with full storyboards |
| `video_prompt_generator` | Produces 5 creative variation prompts per video ad concept |
| `image_prompt_generator` | Produces 5 creative variation prompts per image ad concept |

## Prerequisites

- Python 3.12+
- An [Anthropic API key](https://console.anthropic.com/)

## Setup

1. **Clone the repository**

   ```bash
   git clone <repo-url>
   cd clipping-agent
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your API key**

   Create a `.env` file in the project root:

   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

## Usage

```bash
python main.py
```

You'll be prompted for:

- **Brand URL** — the DTC brand's website (required)
- **Campaign intent** — optional context about the campaign goal

The system then runs through its workflow automatically:

1. **Brand Research** — builds a brand profile and identifies competitors
2. **Parallel Analysis** — audits the brand's ads and all 5 competitors simultaneously
3. **Concept Generation** — creates 10 ad concepts (5 content types x 2 each) with full storyboards
4. **Concept Selection** — presents a numbered list; you choose which concepts to produce
5. **Production Prompts** — generates 5 creative variations per selected concept as markdown files
6. **Feedback Loop** — refine concepts or prompts through conversation

Type `exit` or `quit` to end the session.

## Output

All output is written to `sessions/`:

```
sessions/
  ad_concepts_20260219_120000/
    ad_concepts.json                  # Full structured output (brand, competitors, concepts)
    the_stack_that_tells_my_story/
      video/
        intimate_handheld_closeup.md
        golden_hour_cinematic.md
        ...
      image/
        thumbnail_hero_shot.md
        ...
    graduation_stack/
      minimal_flat_lay.md
      lifestyle_on_model.md
      ...
```

Each variation markdown contains a paste-ready generation prompt plus a full production breakdown (shot types, lighting, color grading, etc.) — model-agnostic, works with any AI video/image generation tool.

## Project Structure

```
clipping-agent/
  agents/
    __init__.py
    brand_consultant.py          # Orchestrator prompt and agent registry
    brand_researcher.py
    brand_ad_analyzer.py
    competitor_ad_analyzer.py
    ad_concept_generator.py
    video_prompt_generator.py
    image_prompt_generator.py
  models.py                      # Pydantic models and JSON schema
  main.py                        # CLI entry point
  requirements.txt
  .env                           # API key (not committed)
```
