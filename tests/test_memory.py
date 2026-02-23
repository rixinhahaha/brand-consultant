"""
Tests for memory.py — save/load round-trips for all model types and slugify edge cases.

Usage:
    pytest tests/                     # run all tests
    pytest tests/test_memory.py       # run just memory tests
    pytest tests/test_memory.py -v    # verbose output
    pytest tests/test_memory.py -k "TestSlugify"  # run a single test class
"""

import shutil

import pytest

from memory import (
    PROJECT_DIR,
    list_known_brands,
    load_brand_ad_audit,
    load_category_memory,
    load_competitor_entry,
    save_brand_ad_audit,
    save_brand_memory,
    save_category_memory,
    save_competitor_entry,
    slugify,
)
from models import (
    AdType,
    BrandAdAnalysis,
    BrandAdAuditMemory,
    BrandAdFormat,
    BrandMemory,
    BrandProfile,
    BuyerPersona,
    CategoryMemory,
    CompetitorMemoryEntry,
    ProductEntry,
    TrendingFormat,
    ViralAdPattern,
    VisualIdentity,
)


# ── Fixtures ──

TEST_MEMORY_DIR = PROJECT_DIR / "memory"


@pytest.fixture(autouse=True)
def clean_test_memory():
    """Remove test-specific memory directories after each test."""
    yield
    # Clean up test brand/category dirs created during tests
    for slug in ("test_brand", "test_brand_2"):
        d = TEST_MEMORY_DIR / "brands" / slug
        if d.exists():
            shutil.rmtree(d)
    for slug in ("test_category",):
        d = TEST_MEMORY_DIR / "categories" / slug
        if d.exists():
            shutil.rmtree(d)


def _brand_profile() -> BrandProfile:
    return BrandProfile(
        name="Test Brand",
        instagram="@testbrand",
        vibe=["minimal", "modern"],
        category="test widgets",
        price_range="$10-$50",
        materials="recycled plastic",
        tone="friendly",
        usp="The best test widgets.",
    )


def _brand_memory() -> BrandMemory:
    return BrandMemory(
        brand=_brand_profile(),
        category_slug="test_category",
        last_updated="2026-02-22",
        visual_identity=VisualIdentity(
            primary_colors=["#000000", "#FFFFFF"],
            color_palette=["#000000", "#FFFFFF", "#FF0000"],
            typography_style="sans-serif",
            photography_style="flat lay",
            lighting_preference="natural",
            overall_aesthetic="clean and minimal",
        ),
        products=[
            ProductEntry(
                name="Widget A",
                description="A great widget",
                price="$25",
                image_uri="https://example.com/widget-a.jpg",
                key_features=["durable", "lightweight"],
            )
        ],
    )


def _brand_ad_audit() -> BrandAdAuditMemory:
    return BrandAdAuditMemory(
        brand_slug="test_brand",
        last_updated="2026-02-22",
        ad_audit=BrandAdAnalysis(
            ad_formats=[
                BrandAdFormat(
                    type="product showcase carousel",
                    description="Clean flat-lay shots",
                    platform="Meta Ad Library",
                )
            ],
            visual_style="Clean, minimal, high-contrast photography",
            hooks=["Start with a question", "Before/after reveal"],
            strategy_gaps=["No UGC content", "Missing comparison ads"],
        ),
        historical_gaps=["No video content"],
    )


def _competitor_entry() -> CompetitorMemoryEntry:
    return CompetitorMemoryEntry(
        name="Rival Co",
        slug="rival_co",
        instagram="@rivalco",
        why="Direct competitor in test widgets",
        ad_types=[
            AdType(
                type="UGC testimonial reel",
                description="Customer shows product in daily life",
                why_it_works="Authentic social proof",
            )
        ],
        visual_style="Bright, colorful, playful",
        hooks=["Wait for it...", "POV: you just found..."],
        buyer_personas_targeted=["Budget-Conscious Tester"],
        viral_patterns=["Before/After Reveal"],
        last_researched="2026-02-22",
    )


def _category_memory() -> CategoryMemory:
    return CategoryMemory(
        category="Test Widgets",
        category_slug="test_category",
        last_updated="2026-02-22",
        competitors=[_competitor_entry()],
        trending_formats=[
            TrendingFormat(
                format="UGC Reels",
                description="User-generated content in reel format",
                which_brands=["Rival Co"],
            )
        ],
        viral_ad_patterns=[
            ViralAdPattern(
                pattern_name="Before/After Reveal",
                description="Show product transformation",
                why_it_works="Creates curiosity gap",
                example_brands=["Rival Co"],
                estimated_engagement="high",
            )
        ],
        buyer_personas=[
            BuyerPersona(
                label="Budget-Conscious Tester",
                description="Looks for value. Reads reviews. Compares options.",
                age_range="25-35",
                psychographics=["value-driven", "research-oriented"],
                purchase_drivers=["price", "reviews"],
                brands_targeting=["Rival Co"],
            )
        ],
    )


# ── slugify tests ──


class TestSlugify:
    def test_basic(self):
        assert slugify("Alex and Ani") == "alex_and_ani"

    def test_single_word(self):
        assert slugify("Gorjana") == "gorjana"

    def test_strips_special_chars(self):
        assert slugify("  Pura Vida  Bracelets! ") == "pura_vida_bracelets"

    def test_numbers_preserved(self):
        assert slugify("Brand 123") == "brand_123"

    def test_multiple_spaces(self):
        assert slugify("hello    world") == "hello_world"

    def test_empty_string(self):
        assert slugify("") == ""

    def test_only_special_chars(self):
        assert slugify("!!!@@@") == ""

    def test_hyphens_removed(self):
        assert slugify("some-brand-name") == "somebrandname"

    def test_url_like(self):
        assert slugify("alexandani") == "alexandani"


# ── Brand memory round-trip ──


class TestBrandMemory:
    def test_save_and_load(self):
        mem = _brand_memory()
        path = save_brand_memory(mem)
        assert path.exists()

        brands = list_known_brands()
        loaded = next((b for b in brands if b.brand.name == "Test Brand"), None)
        assert loaded is not None
        assert loaded.brand.name == "Test Brand"
        assert loaded.category_slug == "test_category"
        assert loaded.visual_identity is not None
        assert loaded.visual_identity.primary_colors == ["#000000", "#FFFFFF"]
        assert len(loaded.products) == 1

    def test_load_nonexistent(self):
        brands = list_known_brands()
        assert not any(b.brand.name == "nonexistent_brand_xyz" for b in brands)


# ── Brand ad audit round-trip ──


class TestBrandAdAudit:
    def test_save_and_load(self):
        audit = _brand_ad_audit()
        path = save_brand_ad_audit(audit)
        assert path.exists()

        loaded = load_brand_ad_audit("test_brand")
        assert loaded is not None
        assert loaded.brand_slug == "test_brand"
        assert len(loaded.ad_audit.ad_formats) == 1
        assert loaded.historical_gaps == ["No video content"]

    def test_load_nonexistent(self):
        assert load_brand_ad_audit("nonexistent_brand_xyz") is None


# ── Category memory round-trip ──


class TestCategoryMemory:
    def test_save_and_load(self):
        # Save competitor entry first — load_category_memory reassembles from individual files
        save_competitor_entry("test_category", _competitor_entry())

        mem = _category_memory()
        path = save_category_memory(mem)
        assert path.exists()

        loaded = load_category_memory("test_category")
        assert loaded is not None
        assert loaded.category == "Test Widgets"
        assert len(loaded.competitors) == 1
        assert len(loaded.viral_ad_patterns) == 1
        assert len(loaded.buyer_personas) == 1

    def test_load_nonexistent(self):
        assert load_category_memory("nonexistent_cat_xyz") is None


# ── Competitor entry round-trip ──


class TestCompetitorEntry:
    def test_save_and_load(self):
        entry = _competitor_entry()
        path = save_competitor_entry("test_category", entry)
        assert path.exists()

        loaded = load_competitor_entry("test_category", "rival_co")
        assert loaded is not None
        assert loaded.name == "Rival Co"
        assert len(loaded.ad_types) == 1
        assert loaded.buyer_personas_targeted == ["Budget-Conscious Tester"]

    def test_load_nonexistent(self):
        assert load_competitor_entry("test_category", "no_such_competitor") is None


# ── Pydantic validation ──


class TestModelValidation:
    def test_category_memory_from_json(self):
        mem = _category_memory()
        json_str = mem.model_dump_json()
        loaded = CategoryMemory.model_validate_json(json_str)
        assert loaded.category_slug == "test_category"

    def test_brand_memory_optional_fields(self):
        """BrandMemory works without optional visual_identity and products."""
        mem = BrandMemory(
            brand=_brand_profile(),
            category_slug="test_category",
            last_updated="2026-02-22",
        )
        assert mem.visual_identity is None
        assert mem.products == []

        json_str = mem.model_dump_json()
        loaded = BrandMemory.model_validate_json(json_str)
        assert loaded.visual_identity is None

    def test_competitor_entry_default_lists(self):
        """CompetitorMemoryEntry works with empty persona/pattern lists."""
        entry = CompetitorMemoryEntry(
            name="Basic Co",
            slug="basic_co",
            instagram="@basicco",
            why="Competitor",
            ad_types=[],
            visual_style="Simple",
            hooks=["Hook 1"],
            last_researched="2026-02-22",
        )
        assert entry.buyer_personas_targeted == []
        assert entry.viral_patterns == []
