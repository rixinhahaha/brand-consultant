"""
Formatting utilities for ad content generator output.
All print/display functions for CLI output.
"""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ad_content_generator import (
        AdConcept,
        AdConceptsOutput,
        AdType,
        BrandProfile,
        Competitor,
        CompetitorAds,
        ContentType,
        StoryboardScene,
        TrendingFormat,
    )


# ═════════════════════════════════════════════
# Display — Primitives
# ═════════════════════════════════════════════


def print_stage(n: int, title: str) -> None:
    bar = "━" * 60
    print(f"\n\033[95m{bar}\033[0m")
    print(f"\033[1;95m  STAGE {n}  │  {title}\033[0m")
    print(f"\033[95m{bar}\033[0m\n")


def print_status(msg: str) -> None:
    print(f"  \033[90m→ {msg}\033[0m")


def print_done(msg: str) -> None:
    print(f"  \033[92m✓ {msg}\033[0m")


def print_error(msg: str) -> None:
    print(f"  \033[91m✗ {msg}\033[0m")


def print_section(text: str) -> None:
    print(f"\n\033[1;97m{'─' * 60}\033[0m")
    print(f"\033[1;97m  {text}\033[0m")
    print(f"\033[1;97m{'─' * 60}\033[0m")


def print_label(text: str) -> None:
    print(f"\n  \033[1;96m{text}\033[0m")


def print_wrapped(text: str, indent: int = 4) -> None:
    for line in textwrap.wrap(text, width=70):
        print(f"{' ' * indent}{line}")


def print_banner() -> None:
    print("\n\033[1;97m" + "═" * 60)
    print("   AD CONTENT GENERATOR — Agentic Workflow (LangChain)")
    print("═" * 60 + "\033[0m")
    print("  Competitor ads → Content types → Storyboards\n")


# ═════════════════════════════════════════════
# Display — Data printers
# ═════════════════════════════════════════════


def print_brand(brand: BrandProfile) -> None:
    print_done(f"Brand: {brand.name}")
    print(f"    Vibe:      {', '.join(brand.vibe)}")
    print(f"    Category:  {brand.category}")
    print(f"    Materials: {brand.materials}")
    print(f"    Price:     {brand.price_range}")
    print(f"    Tone:      {brand.tone}")
    print(f"    USP:       {brand.usp}")


def print_competitors(competitors: list[Competitor]) -> None:
    print()
    print_done(f"Found {len(competitors)} competitors:")
    for c in competitors:
        print(f"    • {c.name}  {c.instagram}")
        print(f"      {c.why}")


def print_ad_type(at: AdType) -> None:
    print(f"\n    \033[97m{at.type}\033[0m")
    print_wrapped(at.description, indent=6)
    print(f"      \033[90mWhy it works: {at.why_it_works}\033[0m")


def print_competitor_ads(ca: CompetitorAds) -> None:
    print_label(ca.brand)
    print(f"    Visual style: {ca.visual_style}")
    if ca.hooks:
        print(f"    Hooks: {' | '.join(ca.hooks[:3])}")
    for at in ca.ad_types:
        print_ad_type(at)


def print_trending_formats(formats: list[TrendingFormat]) -> None:
    if not formats:
        return
    print()
    print_done("Trending formats:")
    for t in formats:
        print(f"    📈 \033[93m{t.format}\033[0m — {t.description}")
        print(f"       Used by: {', '.join(t.which_brands)}")


def print_scene(scene: StoryboardScene) -> None:
    print(f"    │")
    print(f"    │  \033[93m━━ SCENE {scene.scene}\033[0m  \033[90m({scene.duration_seconds}s)\033[0m")

    vis_lines = textwrap.wrap(scene.visual, width=52)
    print(f"    │  \033[97m🎥 Visual:\033[0m {vis_lines[0]}")
    for vl in vis_lines[1:]:
        print(f"    │             {vl}")

    aud_lines = textwrap.wrap(scene.audio_or_text, width=52)
    print(f"    │  \033[97m🔊 Audio:\033[0m  {aud_lines[0]}")
    for al in aud_lines[1:]:
        print(f"    │             {al}")


def print_storyboard(storyboard: list[StoryboardScene]) -> None:
    total_dur = sum(s.duration_seconds for s in storyboard)
    print(f"    │  \033[1;96m📋 STORYBOARD\033[0m")
    print(f"    │  \033[90m{len(storyboard)} scenes · {total_dur}s total\033[0m")
    for scene in storyboard:
        print_scene(scene)


def print_ad_copy(ad: AdConcept) -> None:
    print(f"    │")
    print(f"    │  \033[1;96m✍️  AD COPY\033[0m")
    copy_lines = textwrap.wrap(ad.copy, width=52)
    print(f'    │  "{copy_lines[0]}')
    for cl in copy_lines[1:]:
        print(f"    │   {cl}")
    print(f"    │")
    print(f"    │  \033[1;92m▶ CTA:\033[0m {ad.cta}")
    if ad.reference:
        print(f"    │  \033[90m↳ {ad.reference}\033[0m")


def print_ad_concept(j: int, ad: AdConcept) -> None:
    print()
    print(f"    \033[1;97m┌─ Ad {j}: {ad.title}\033[0m  \033[35m[{ad.format}]\033[0m")
    print(f"    │")
    print_storyboard(ad.storyboard)
    print_ad_copy(ad)
    print(f"    └{'─' * 52}")


def print_content_type(i: int, ct: ContentType) -> None:
    print_section(f"#{i}  {ct.name}")
    print(f"    \033[90m{ct.hook}\033[0m")

    fmts = "  ".join(f"\033[35m[{f}]\033[0m" for f in ct.formats)
    print(f"    Formats: {fmts}")

    print(f"\n    \033[90mWhy it works:\033[0m")
    print_wrapped(ct.why_it_works)

    for j, ad in enumerate(ct.ads, 1):
        print_ad_concept(j, ad)

    if ct.hashtags:
        tags = "  ".join(ct.hashtags)
        print(f"\n    \033[90m# {tags}\033[0m")


def print_playbook(results: AdConceptsOutput) -> None:
    print_stage(4, "YOUR AD CONTENT PLAYBOOK")

    if results.production_notes:
        print_label("🎬  CREATIVE DIRECTION")
        print_wrapped(results.production_notes)

    for i, ct in enumerate(results.content_types, 1):
        print_content_type(i, ct)


def print_saved(path: str) -> None:
    print(f"\n  \033[92m✓ Full structured output saved to {path}\033[0m")
    print(f"  \033[90mRun again anytime to regenerate.\033[0m\n")
