"""
Ad Content Generator — Agentic Workflow (Anthropic SDK)
======================================================
Analyzes competitor ad formats via web search, then generates
tailored ad concepts with full storyboards for your brand.

Uses Anthropic Messages API (beta) with web search tool and
structured outputs (Pydantic JSON schema).

Requirements:
    pip install anthropic pydantic python-dotenv

Usage:
    Either set ANTHROPIC_API_KEY in .env, or: export ANTHROPIC_API_KEY=sk-ant-...
    python ad_content_generator.py
"""

import json
import sys
from pathlib import Path

# Load .env before Anthropic client reads ANTHROPIC_API_KEY
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

from pydantic import BaseModel, Field
import anthropic

from formatting import (
    print_banner,
    print_brand,
    print_competitor_ads,
    print_competitors,
    print_done,
    print_error,
    print_playbook,
    print_saved,
    print_stage,
    print_status,
    print_trending_formats,
)


# ═════════════════════════════════════════════
# Pydantic Models
# ═════════════════════════════════════════════

# ── Stage 1: Brand + Competitors ──

class BrandProfile(BaseModel):
    """Profile of a DTC brand's identity and product."""
    name: str = Field(description="Brand name")
    vibe: list[str] = Field(description="3-5 aesthetic adjectives describing the brand's visual and tonal identity")
    category: str = Field(description="Product category, e.g. 'sustainable backpacks'")
    price_range: str = Field(description="Approximate price range, e.g. '$80-$150'")
    materials: str = Field(description="Key materials used, e.g. 'recycled PET ripstop'")
    tone: str = Field(description="Brand tone of voice, e.g. 'warm, playful, eco-conscious'")
    usp: str = Field(description="Unique selling proposition in one sentence")


class Competitor(BaseModel):
    """A competing brand."""
    name: str = Field(description="Competitor brand name")
    instagram: str = Field(description="Instagram handle, e.g. '@brandname'")
    why: str = Field(description="One sentence on why they are a relevant competitor")


class BrandAnalysis(BaseModel):
    """Brand understanding and competitive landscape."""
    brand: BrandProfile
    competitors: list[Competitor] = Field(description="5 competitor brands")


# ── Stage 2: Competitor Ad Formats ──

class AdType(BaseModel):
    """A specific ad format used by a competitor."""
    type: str = Field(description="Descriptive name of the ad format, e.g. 'UGC testimonial reel'")
    description: str = Field(description="What the ad looks like — shot style, structure, visuals")
    why_it_works: str = Field(description="Why this format drives engagement or conversions")


class CompetitorAds(BaseModel):
    """Ad creative analysis for a single competitor."""
    brand: str = Field(description="Brand name")
    ad_types: list[AdType] = Field(description="2-4 distinct ad formats this brand uses")
    visual_style: str = Field(description="Overall visual language — color palette, lighting, editing style")
    hooks: list[str] = Field(description="2-3 common first-3-second hooks they use")


class TrendingFormat(BaseModel):
    """An ad format trending across the category."""
    format: str = Field(description="Name of the trending format")
    description: str = Field(description="What it looks like and how it works")
    which_brands: list[str] = Field(description="Which competitor brands use this format")


class CompetitorAdAnalysis(BaseModel):
    """Full competitor ad format research."""
    competitor_ads: list[CompetitorAds] = Field(description="Ad format analysis per competitor")
    trending_formats: list[TrendingFormat] = Field(description="3-5 formats trending across the category")


# ── Stage 3: Generated Ad Concepts ──

class StoryboardScene(BaseModel):
    """A single scene in an ad storyboard."""
    scene: int = Field(description="Scene number, starting from 1")
    visual: str = Field(description="What the viewer sees — camera angle, subject, action, setting")
    audio_or_text: str = Field(description="Voiceover, music note, sound effect, or text overlay shown on screen")
    duration_seconds: int = Field(description="Duration of this scene in seconds")


class AdConcept(BaseModel):
    """A specific ad concept with full storyboard."""
    title: str = Field(description="Descriptive title for the ad concept")
    format: str = Field(description="Ad format: Reel, Carousel, Static, Video, Story, or UGC")
    storyboard: list[StoryboardScene] = Field(description="3-5 scenes making up the full ad")
    copy: str = Field(description="Suggested ad caption or copy, under 25 words")
    cta: str = Field(description="Call to action, e.g. 'Shop Now', 'Learn More'")
    reference: str = Field(description="Which competitor format inspired this and what was adapted")


class ContentType(BaseModel):
    """A repeatable content category with ad concepts."""
    name: str = Field(description="Content category name, e.g. 'Process Reveal Reels'")
    hook: str = Field(description="One-line summary of what this content type is")
    why_it_works: str = Field(description="Why this format works for this specific brand, referencing competitor evidence")
    formats: list[str] = Field(description="Which ad formats this category uses, e.g. ['Reel', 'Carousel']")
    ads: list[AdConcept] = Field(description="2 specific ad concepts with full storyboards")
    hashtags: list[str] = Field(description="3-5 relevant hashtags for this content type")


class AdConceptsOutput(BaseModel):
    """Complete ad content playbook."""
    content_types: list[ContentType] = Field(description="5 distinct content type categories")
    production_notes: str = Field(description="2-3 sentences on overall creative direction — color grading, music style, visual language")


# ═════════════════════════════════════════════
# Anthropic client and helpers
# ═════════════════════════════════════════════

MODEL = "claude-sonnet-4-6"

# Web search tool for research stages (server-side; API executes searches)
WEB_SEARCH_TOOL: dict = {"type": "web_search_20250305", "name": "web_search"}


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic()


def _extract_text_from_content(content: list) -> str:
    """Collect all text from assistant content blocks."""
    parts: list[str] = []
    for block in content:
        if getattr(block, "type", None) == "text" and hasattr(block, "text"):
            parts.append(block.text)
    return "\n\n".join(parts).strip() if parts else ""


def _run_with_web_search(system: str, user_content: str, max_tokens: int = 4096) -> str:
    """Call beta messages with web search tool; return final assistant text. API executes searches within a single request."""
    client = _client()
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_content}],
        tools=[WEB_SEARCH_TOOL],
        betas=["messages-api-with-search-2025-03-05"],
    )
    return _extract_text_from_content(response.content)


def _structured_call(system: str, user_content: str, output_format: type[BaseModel], max_tokens: int = 4096) -> BaseModel:
    """Call beta messages parse with structured output (no tools)."""
    client = _client()
    msg = client.beta.messages.parse(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_content}],
        output_format=output_format,
        betas=["structured-outputs-2025-12-15"],
    )
    parsed = msg.parsed_output
    if parsed is None:
        text = _extract_text_from_content(msg.content)
        return output_format.model_validate_json(text)
    return parsed


# ═════════════════════════════════════════════
# Stage 1: Scan brand + find competitors
# ═════════════════════════════════════════════

def scan_brand(brand_url: str, campaign_intent: str = "") -> BrandAnalysis:
    print_stage(1, "SCAN BRAND & FIND COMPETITORS")
    print_status(f"Searching the web for: {brand_url}")

    user_msg = f"Analyze this brand and find 5 competitors: {brand_url}"
    if campaign_intent:
        user_msg += f"\n\nCampaign intent: {campaign_intent}"

    system = (
        "You are a DTC brand analyst. Search the web to understand the "
        "given brand's identity, products, and audience. Then find 5 "
        "competitor brands that sell similar products to a similar audience. "
        "Summarize your findings clearly."
    )
    research_text = _run_with_web_search(system, user_msg)

    print_status("Structuring brand data...")
    data = _structured_call(
        system="Extract the brand profile and 5 competitors from the research below. If information is missing, make reasonable inferences.",
        user_content=research_text,
        output_format=BrandAnalysis,
    )
    assert isinstance(data, BrandAnalysis)
    print_brand(data.brand)
    print_competitors(data.competitors)
    return data


# ═════════════════════════════════════════════
# Stage 2: Analyze competitor ad formats
# ═════════════════════════════════════════════

def analyze_ads(brand_data: BrandAnalysis) -> CompetitorAdAnalysis:
    print_stage(2, "ANALYZE COMPETITOR AD FORMATS")

    comp_names = ", ".join(c.name for c in brand_data.competitors)
    print_status(f"Researching ad creative for: {comp_names}")

    system = (
        "You are a paid social creative strategist. Research the given brands' "
        "Instagram and Facebook ad creative execution. Focus on ad formats "
        "(video, carousel, static, UGC, stories), visual styles, first-3-second "
        "hooks, and viral content patterns. Do NOT discuss brand positioning — "
        "only describe what the ads actually look and feel like."
    )
    user_content = (
        f"Research the ad creative formats used by: {comp_names}\n"
        f"Category: {brand_data.brand.category}\n\n"
        f"Search for their Meta Ad Library entries, Instagram content, "
        f"and any marketing analysis about their ad creative."
    )
    research_text = _run_with_web_search(system, user_content)

    print_status("Structuring competitor ad data...")
    data = _structured_call(
        system="Extract the competitor ad format analysis from the research below. Focus on creative execution — what the ads look like, not brand strategy.",
        user_content=research_text,
        output_format=CompetitorAdAnalysis,
    )
    assert isinstance(data, CompetitorAdAnalysis)
    for ca in data.competitor_ads:
        print_competitor_ads(ca)
    print_trending_formats(data.trending_formats)
    return data


# ═════════════════════════════════════════════
# Stage 3: Generate ad concepts
# ═════════════════════════════════════════════

def generate_concepts(brand_data: BrandAnalysis, ad_data: CompetitorAdAnalysis) -> AdConceptsOutput:
    print_stage(3, "GENERATE AD CONCEPTS")

    brand = brand_data.brand
    print_status(f"Creating content types for {brand.name}...")

    comp_summary = "\n".join(
        f"- {ca.brand}: {', '.join(at.type for at in ca.ad_types)} "
        f"(style: {ca.visual_style})"
        for ca in ad_data.competitor_ads
    )
    trends = ", ".join(t.format for t in ad_data.trending_formats)

    system = (
        "You are an elite creative director at a top DTC performance marketing "
        "agency. Take the competitor ad formats that work and adapt them for "
        "the given brand's vibe, products, and audience. Don't just copy — "
        "translate each format into something that feels native to this brand.\n\n"
        "Generate exactly 5 content types, each with exactly 2 ad concepts. "
        "Every ad must have a detailed storyboard with 3-5 scenes."
    )
    user_content = (
        f"BRAND: {brand.name}\n"
        f"VIBE: {', '.join(brand.vibe)}\n"
        f"CATEGORY: {brand.category}\n"
        f"MATERIALS: {brand.materials}\n"
        f"USP: {brand.usp}\n"
        f"TONE: {brand.tone}\n"
        f"PRICE: {brand.price_range}\n\n"
        f"COMPETITOR AD FORMATS:\n{comp_summary}\n\n"
        f"TRENDING FORMATS: {trends}\n\n"
        f"Generate 5 content types × 2 ads each with full storyboards."
    )
    data = _structured_call(
        system=system,
        user_content=user_content,
        output_format=AdConceptsOutput,
        max_tokens=8000,
    )
    assert isinstance(data, AdConceptsOutput)
    total = sum(len(ct.ads) for ct in data.content_types)
    print_done(f"Generated {len(data.content_types)} content types with {total} ad concepts")
    return data


# ═════════════════════════════════════════════
# Orchestration
# ═════════════════════════════════════════════

def save_output(brand_data: BrandAnalysis, ad_data: CompetitorAdAnalysis, results: AdConceptsOutput):
    path = "ad_concepts_output.json"
    output = {
        "brand_analysis": brand_data.model_dump(),
        "competitor_ads": ad_data.model_dump(),
        "ad_concepts": results.model_dump(),
    }
    with open(path, "w") as f:
        json.dump(output, f, indent=2)
    print_saved(path)


def main():
    print_banner()

    brand_url = input("  \033[1mBrand URL:\033[0m ").strip()
    if not brand_url:
        print("  Please provide a brand URL.")
        sys.exit(1)

    campaign_intent = input("  \033[1mCampaign intent\033[0m (optional): ").strip()

    try:
        brand_data = scan_brand(brand_url, campaign_intent)
        ad_data = analyze_ads(brand_data)
        results = generate_concepts(brand_data, ad_data)

        print_playbook(results)
        save_output(brand_data, ad_data, results)

    except KeyboardInterrupt:
        print("\n\n  Cancelled.")
    except Exception as e:
        print_error(str(e))
        raise


if __name__ == "__main__":
    main()
