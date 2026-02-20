"""
Pydantic models for ad content generator.
Pydantic models for the multi-agent ad content generator.
"""

import json

from pydantic import BaseModel, Field


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


# ── Stage 2a: Brand's Own Ad Audit (new) ──

class BrandAdFormat(BaseModel):
    """A specific ad format used by the brand itself."""
    type: str = Field(description="Descriptive name of the ad format, e.g. 'product showcase carousel'")
    description: str = Field(description="What the ad looks like — shot style, structure, visuals")
    platform: str = Field(description="Platform where this ad was found, e.g. 'Meta Ad Library', 'Instagram'")


class BrandAdAnalysis(BaseModel):
    """Audit of the brand's own advertising creative."""
    ad_formats: list[BrandAdFormat] = Field(description="Ad formats the brand currently uses")
    visual_style: str = Field(description="Overall visual language — color palette, lighting, editing style")
    hooks: list[str] = Field(description="2-3 common hooks or opening patterns in their ads")
    strategy_gaps: list[str] = Field(description="2-3 identified gaps or missed opportunities in their current ad strategy")


# ── Stage 2b: Competitor Ad Formats ──

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
    negative_prompts: list[str] = Field(description="3-5 things to avoid in production — wrong aesthetics, off-brand elements, common AI artifacts")
    post_production_notes: str = Field(description="Concept-specific post-production direction — transitions, color grading, music sync, text overlay timing")


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


# ── Full Output Envelope ──

class FullOutput(BaseModel):
    """Complete JSON output schema for the timestamped output files."""
    brand_analysis: BrandAnalysis
    brand_ad_audit: BrandAdAnalysis
    competitor_ads: CompetitorAdAnalysis
    ad_concepts: AdConceptsOutput


def full_output_json_schema() -> str:
    """Return the FullOutput JSON schema as a formatted string for use in agent prompts."""
    return json.dumps(FullOutput.model_json_schema(), indent=2)
