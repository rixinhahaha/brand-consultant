"""
Pydantic models for ad content generator.
Pydantic models for the multi-agent ad content generator.
"""

from pydantic import BaseModel, Field


# ── Stage 1: Brand + Competitors ──

class BrandProfile(BaseModel):
    """Profile of a DTC brand's identity and product."""
    name: str = Field(description="Brand name")
    instagram: str = Field(description="Instagram handle, e.g. '@brandname'")
    vibe: list[str] = Field(description="3-5 aesthetic adjectives describing the brand's visual and tonal identity")
    category: str = Field(description="Product category, e.g. 'sustainable backpacks'")
    price_range: str = Field(description="Approximate price range, e.g. '$80-$150'")
    materials: str = Field(description="Key materials used, e.g. 'recycled PET ripstop'")
    tone: str = Field(description="Brand tone of voice, e.g. 'warm, playful, eco-conscious'")
    usp: str = Field(description="Unique selling proposition in one sentence")


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


class TrendingFormat(BaseModel):
    """An ad format trending across the category."""
    format: str = Field(description="Name of the trending format")
    description: str = Field(description="What it looks like and how it works")
    which_brands: list[str] = Field(description="Which competitor brands use this format")


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
    storyboard: list[StoryboardScene] = Field(description="5-7 scenes making up the full ad")
    copy: str = Field(description="Suggested ad caption or copy, under 25 words")
    cta: str = Field(description="Call to action, e.g. 'Shop Now', 'Learn More'")
    reference: str = Field(description="Which competitor format inspired this and what was adapted")
    product_placement_notes: str = Field(default="", description="How and where products should appear in the ad — specific placement, angles, moments")
    talent_direction: str = Field(default="", description="Direction for talent/models — mood, energy, wardrobe, casting notes")


# ── Stored Ad Concept (per-concept memory) ──

class StoredAdConcept(BaseModel):
    """A single ad concept stored in brand memory."""
    content_type: str
    content_type_hook: str
    why_it_works: str
    campaign_intent: str
    created_date: str
    hashtags: list[str]
    concept: AdConcept


# ── Memory: Category (shared) ──

class BuyerPersona(BaseModel):
    """A buyer persona observed across the category."""
    label: str = Field(description="e.g., 'The Symbolic Self-Purchaser'")
    description: str = Field(description="2-3 sentence profile")
    age_range: str
    psychographics: list[str]
    purchase_drivers: list[str]
    brands_targeting: list[str] = Field(description="Which competitors target this persona")


class ViralAdPattern(BaseModel):
    """A viral/high-performing ad pattern in the category."""
    pattern_name: str
    description: str
    why_it_works: str
    example_brands: list[str]
    estimated_engagement: str = Field(description="e.g., 'high', 'very high'")


class CompetitorMemoryEntry(BaseModel):
    """Persisted competitor analysis."""
    name: str
    slug: str
    instagram: str
    why: str
    ad_types: list[AdType]
    visual_style: str
    hooks: list[str]
    buyer_personas_targeted: list[str] = Field(default_factory=list, description="References to BuyerPersona labels")
    viral_patterns: list[str] = Field(default_factory=list, description="References to ViralAdPattern names")
    last_researched: str = Field(description="ISO date")
    organic_content_formats: list[str] = Field(default_factory=list, description="Organic content formats used on social media")
    content_cadence: dict | None = Field(default=None, description="Posting frequency and schedule patterns")
    ugc_creator_strategy: dict | None = Field(default=None, description="UGC and creator partnership strategy")
    creative_testing_patterns: dict | None = Field(default=None, description="A/B testing and creative iteration patterns")
    spend_signals: dict | None = Field(default=None, description="Estimated spend signals and budget indicators")


class CategoryMemory(BaseModel):
    """Shared memory for a product category."""
    category: str
    category_slug: str
    last_updated: str
    competitors: list[CompetitorMemoryEntry] = Field(default_factory=list)
    trending_formats: list[TrendingFormat] = Field(default_factory=list)
    viral_ad_patterns: list[ViralAdPattern] = Field(default_factory=list)
    buyer_personas: list[BuyerPersona] = Field(default_factory=list)
    competitive_synthesis: dict | None = Field(default=None, description="Cross-competitor synthesis: patterns, whitespace, persona mapping")


class CategoryMemoryFile(BaseModel):
    """On-disk format for category.json — stores competitor slugs instead of full objects."""
    category: str
    category_slug: str
    last_updated: str
    competitor_slugs: list[str] = Field(default_factory=list)
    trending_formats: list[TrendingFormat] = Field(default_factory=list)
    viral_ad_patterns: list[ViralAdPattern] = Field(default_factory=list)
    buyer_personas: list[BuyerPersona] = Field(default_factory=list)
    competitive_synthesis: dict | None = Field(default=None, description="Cross-competitor synthesis: patterns, whitespace, persona mapping")


# ── Memory: Brand (private) ──

class VisualIdentity(BaseModel):
    """Persistent brand visual identity."""
    primary_colors: list[str]
    color_palette: list[str]
    typography_style: str
    photography_style: str
    lighting_preference: str
    overall_aesthetic: str


class ProductEntry(BaseModel):
    """A product in the brand catalog."""
    name: str
    description: str
    price: str
    image_uri: str
    key_features: list[str]


class BrandMemory(BaseModel):
    """Private brand-specific memory."""
    brand: BrandProfile
    category_slug: str
    last_updated: str
    visual_identity: VisualIdentity | None = None
    products: list[ProductEntry] = Field(default_factory=list)


class BrandAdAuditMemory(BaseModel):
    """Persisted brand ad audit."""
    brand_slug: str
    last_updated: str
    ad_audit: BrandAdAnalysis
    historical_gaps: list[str] = Field(default_factory=list, description="Gaps from prior audits")


# ── Structured Production Guides ──

class SceneProductionGuide(BaseModel):
    """Production guidance for a single video scene."""
    scene_number: int
    scene_title: str
    duration_seconds: int
    shot_type: str
    camera_angle: str
    camera_movement: str
    framing: str
    key_light: str
    light_quality: str
    light_mood: str
    subject: str
    action: str
    expression: str = ""
    background: str
    depth_of_field: str
    color_palette: str
    color_grade: str
    voiceover: str = "None"
    music: str = ""
    text_overlay: str = "None"


class VideoProductionGuide(BaseModel):
    """Structured production guide for a video variation."""
    concept_title: str
    variation_name: str
    variation_slug: str
    format: str
    total_duration_seconds: int
    scene_count: int
    ad_copy: str
    cta: str
    aspect_ratio: str = "9:16"
    brand_visual_direction: str
    generation_prompt: str
    scenes: list[SceneProductionGuide]
    reference_assets: list[str] = Field(default_factory=list)
    style_references: list[str] = Field(default_factory=list)
    negative_prompts: list[str]
    post_production_notes: list[str]


class CarouselCardGuide(BaseModel):
    """Production guide for a single carousel card."""
    card_number: int
    card_title: str
    composition: str
    perspective: str
    visual_flow: str
    primary_subject: str
    positioning: str
    props_styling: str
    setting: str
    surface: str
    text_content: str
    text_placement: str


class ImageProductionGuide(BaseModel):
    """Structured production guide for an image variation."""
    concept_title: str
    variation_name: str
    variation_slug: str
    format: str  # "Static" or "Carousel"
    aspect_ratio: str
    ad_copy: str
    cta: str
    brand_visual_direction: str
    generation_prompt: str
    composition: str
    perspective: str
    framing: str
    focal_point: str
    primary_subject: str
    positioning: str
    props_styling: str
    scale: str
    key_light: str
    fill: str
    color_temperature: str
    light_mood: str
    dominant_colors: list[str]
    accent_colors: list[str]
    grade: str
    setting: str
    surface_backdrop: str
    depth_of_field: str
    text_placement: str
    font_style: str
    text_color: str
    cards: list[CarouselCardGuide] = Field(default_factory=list)
    overall_visual_consistency: str = ""
    reference_assets: list[str] = Field(default_factory=list)
    style_references: list[str] = Field(default_factory=list)
    negative_prompts: list[str]
    post_production_notes: list[str]
