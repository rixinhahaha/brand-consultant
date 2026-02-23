"""
Memory utilities — Pydantic-validated load/save for persistent brand and category memory.

File layout:
  memory/
    brands/{brand_slug}/brand.json
    brands/{brand_slug}/ad_audit.json
    brands/{brand_slug}/ad_concepts/{concept_slug}/concept.json
    categories/{category_slug}/category.json
    categories/{category_slug}/competitors/{competitor_slug}.json
"""

import re
from pathlib import Path

from models import (
    BrandAdAuditMemory,
    BrandMemory,
    CategoryMemory,
    CategoryMemoryFile,
    CompetitorMemoryEntry,
    StoredAdConcept,
)

PROJECT_DIR = Path(__file__).resolve().parent


def slugify(name: str) -> str:
    """Convert a name to a filesystem-safe slug.

    >>> slugify("Alex and Ani")
    'alex_and_ani'
    >>> slugify("Gorjana")
    'gorjana'
    >>> slugify("  Pura Vida  Bracelets! ")
    'pura_vida_bracelets'
    """
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s


def get_memory_dir() -> Path:
    """Return the project-level memory directory."""
    return PROJECT_DIR / "memory"


# ── Brand discovery ──

def list_known_brands() -> list[BrandMemory]:
    """Return all brands that have saved memory, sorted by last_updated descending."""
    brands_dir = get_memory_dir() / "brands"
    if not brands_dir.exists():
        return []
    results = []
    for brand_dir in brands_dir.iterdir():
        if brand_dir.is_dir() and (brand_dir / "brand.json").exists():
            try:
                mem = BrandMemory.model_validate_json((brand_dir / "brand.json").read_text())
                results.append(mem)
            except Exception:
                continue
    results.sort(key=lambda m: m.last_updated, reverse=True)
    return results


# ── Brand memory ──

def _brand_dir(brand_slug: str) -> Path:
    return get_memory_dir() / "brands" / brand_slug



def save_brand_memory(memory: BrandMemory) -> Path:
    slug = slugify(memory.brand.name)
    path = _brand_dir(slug) / "brand.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(memory.model_dump_json(indent=2))
    return path


# ── Brand ad audit ──

def load_brand_ad_audit(brand_slug: str) -> BrandAdAuditMemory | None:
    path = _brand_dir(brand_slug) / "ad_audit.json"
    if not path.exists():
        return None
    return BrandAdAuditMemory.model_validate_json(path.read_text())


def save_brand_ad_audit(audit: BrandAdAuditMemory) -> Path:
    path = _brand_dir(audit.brand_slug) / "ad_audit.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(audit.model_dump_json(indent=2))
    return path


# ── Ad concepts (per-concept memory) ──

def get_ad_concepts_dir(brand_slug: str) -> Path:
    return _brand_dir(brand_slug) / "ad_concepts"


def list_brand_concepts(brand_slug: str) -> list[StoredAdConcept]:
    """Return all stored ad concepts for a brand, sorted by created_date descending."""
    concepts_dir = get_ad_concepts_dir(brand_slug)
    if not concepts_dir.exists():
        return []
    results = []
    for concept_dir in concepts_dir.iterdir():
        concept_file = concept_dir / "concept.json"
        if concept_dir.is_dir() and concept_file.exists():
            try:
                concept = StoredAdConcept.model_validate_json(concept_file.read_text())
                results.append(concept)
            except Exception:
                continue
    results.sort(key=lambda c: c.created_date, reverse=True)
    return results


# ── Category memory ──

def _category_dir(category_slug: str) -> Path:
    return get_memory_dir() / "categories" / category_slug


def load_category_memory(category_slug: str) -> CategoryMemory | None:
    """Load category.json (slugs only) and assemble full CategoryMemory with competitor objects."""
    path = _category_dir(category_slug) / "category.json"
    if not path.exists():
        return None
    file_data = CategoryMemoryFile.model_validate_json(path.read_text())
    competitors = []
    for slug in file_data.competitor_slugs:
        entry = load_competitor_entry(category_slug, slug)
        if entry is not None:
            competitors.append(entry)
    return CategoryMemory(
        category=file_data.category,
        category_slug=file_data.category_slug,
        last_updated=file_data.last_updated,
        competitors=competitors,
        trending_formats=file_data.trending_formats,
        viral_ad_patterns=file_data.viral_ad_patterns,
        buyer_personas=file_data.buyer_personas,
        competitive_synthesis=file_data.competitive_synthesis,
    )


def save_category_memory(memory: CategoryMemory) -> Path:
    """Extract competitor slugs and write the slim CategoryMemoryFile to disk."""
    file_data = CategoryMemoryFile(
        category=memory.category,
        category_slug=memory.category_slug,
        last_updated=memory.last_updated,
        competitor_slugs=[c.slug for c in memory.competitors],
        trending_formats=memory.trending_formats,
        viral_ad_patterns=memory.viral_ad_patterns,
        buyer_personas=memory.buyer_personas,
        competitive_synthesis=memory.competitive_synthesis,
    )
    path = _category_dir(memory.category_slug) / "category.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(file_data.model_dump_json(indent=2))
    return path


# ── Individual competitor entries ──

def load_competitor_entry(
    category_slug: str, competitor_slug: str
) -> CompetitorMemoryEntry | None:
    path = _category_dir(category_slug) / "competitors" / f"{competitor_slug}.json"
    if not path.exists():
        return None
    return CompetitorMemoryEntry.model_validate_json(path.read_text())


def save_competitor_entry(category_slug: str, entry: CompetitorMemoryEntry) -> Path:
    path = _category_dir(category_slug) / "competitors" / f"{entry.slug}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(entry.model_dump_json(indent=2))
    return path
