#!/usr/bin/env python3
"""
The First Wire — Heritage Craft Origin
Auto-generated media creation script using fal.ai API (fal-ai/veo3-1).

Usage:
    python generate_heritage_craft_origin.py [options]

Options:
    --output-dir PATH   Override the default output directory
    --scenes NUMS       Comma-separated scene numbers to generate (e.g. 1,2,4a,4b)
    --dry-run           Print prompts without calling the API
    --retries N         Number of retries per scene (default: 3)

Requirements:
    pip install fal-client requests
    export FAL_KEY=your_fal_api_key
"""

import argparse
import json
import os
import sys
import time
import datetime
from pathlib import Path

try:
    import fal_client
except ImportError:
    print("Error: fal-client not installed. Run: pip install fal-client")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Error: requests not installed. Run: pip install requests")
    sys.exit(1)

# ── Config ───────────────────────────────────────────────────────────────────

CONCEPT_TITLE = "The First Wire"
VARIATION_NAME = "Heritage Craft Origin"
VARIATION_SLUG = "heritage_craft_origin"

MODEL_ENDPOINT = "fal-ai/veo3-1"
ASPECT_RATIO = "16:9"

DEFAULT_OUTPUT_DIR = (
    "/Users/rixinw/Documents/brand-agency/memory/brands/alex_and_ani"
    "/ad_concepts/the_first_wire/outputs/heritage_craft_origin"
)

# ── Brand Visual Direction ────────────────────────────────────────────────────

BRAND_DIRECTION = """\
Warm, tactile, and deeply grounded in craft. This variation foregrounds the \
physical act of making — fingerprints on copper, wood grain of a worktable, \
natural morning light in a New England workshop. The grade is warm amber-gold \
with deep, rich shadows. Every frame should feel like it was found, not \
constructed. The product is incidental to the hands, the light, and the \
intention behind the work. Lean into analog texture: grain, imperfection, \
the weight of real materials.\
"""

# ── Negative Prompts ──────────────────────────────────────────────────────────

NEGATIVE_PROMPTS = (
    "Jewelry held toward camera or presented for display — product must always appear worn or incidental | "
    "Over-saturated colors or artificially vibrant tones that undermine the warm, muted heritage palette | "
    "Fast cuts, jump cuts, or energetic pacing — this film breathes slowly and deliberately | "
    "Smiling for camera, posed expressions, or any talent performing awareness of being filmed | "
    "Digital-clean, sterile, or clinical visual quality — all imperfection and grain is intentional | "
    "Morphing faces, extra fingers, distorted hands, uncanny skin texture or AI-artifact creep in close-up hand shots | "
    "Any visual element that reads as contemporary fast-fashion or trend-driven — this must feel timeless"
)

# ── Product Reference Images ──────────────────────────────────────────────────
# These URLs are attached directly in the API call arguments via image_url for
# scenes where a specific product appears, enabling fal-ai/veo3-1 to use the
# reference image as visual grounding for that scene.

PRODUCT_REFS = {
    "attitude_of_gratitude_bangle": {
        "name": "Attitude of Gratitude Charm Bangle",
        "url": "https://cdn.shopify.com/s/files/1/0269/9558/9223/products/Attitude-Gratitude-Charm-Bangle-Gold-Front-A21EBWAP8RG.jpg",
        "description": (
            "Expandable wire bangle in Rafaelian gold finish. A single affirmation charm "
            "centered on the round-gauge wire. Warm burnished gold tone, slightly textured "
            "surface. Charm is dimensional, not flat. Wire is slender, loops open for sizing."
        ),
    },
    "token_of_love_bangle": {
        "name": "Token of Love Charm Bangle",
        "url": "https://www.alexandani.com/cdn/shop/files/token-of-love-charm-bangle-1-AO250034RSG.jpg",
        "description": (
            "Expandable gold-tone wire bangle with a single love-themed symbolic charm "
            "centered on the wire. Clean and minimal. Warm gold finish. The charm is compact "
            "and sits flush against the wire."
        ),
    },
    "glass_butterfly_bangle": {
        "name": "Glass Butterfly Beaded Charm Bangle",
        "url": "https://www.alexandani.com/cdn/shop/files/glass-butterfly-beaded-charm-bracelet-1-AO251061WSS.jpg",
        "description": (
            "Beaded silver-tone expandable wire bangle. Multiple small beads along the wire, "
            "with a prominent glass butterfly charm as centerpiece. The butterfly wings are "
            "semi-translucent glass — they refract and scatter light when held toward a light "
            "source. Silver finish throughout."
        ),
    },
    "make_your_own_luck_bangle": {
        "name": "Make Your Own Luck Ladybug Charm Bangle",
        "url": "https://www.alexandani.com/cdn/shop/files/lady-bug-opening-charm-bangle-1-AO260175SPSG.jpg",
        "description": (
            "Expandable wire bangle in shiny gold finish. Features a dimensional ladybug charm "
            "with an opening mechanism — red with black spots, sits prominently and "
            "three-dimensionally on the wire. The ladybug charm is the dominant visual element."
        ),
    },
}

# ── Duration Helpers ──────────────────────────────────────────────────────────

def map_duration_veo3(seconds: int) -> str:
    """Round to nearest valid veo3-1 duration: 4s, 6s, or 8s."""
    if seconds <= 5:
        return "4s"
    elif seconds <= 7:
        return "6s"
    else:
        return "8s"

# ── Scene Definitions ─────────────────────────────────────────────────────────
# Each entry is a dict with:
#   scene_id              : unique string key used for filenames
#   title                 : human-readable scene title
#   source_duration       : seconds from the production guide
#   veo3_duration         : mapped veo3-1 duration string
#   prompt                : fully constructed generation prompt
#   is_sub_scene          : True for montage / multi-shot sub-scenes
#   stitch_group          : parent scene key if this is a sub-scene
#   reference_image_url   : product reference image URL, or None if no specific product

SCENES = [
    # ── Scene 1: The Wire ─────────────────────────────────────────────────────
    {
        "scene_id": "scene_1",
        "title": "Scene 1 — The Wire",
        "source_duration": 3,
        "veo3_duration": "4s",
        "is_sub_scene": False,
        "stitch_group": None,
        "reference_image_url": None,  # hands only, no specific product
        "prompt": (
            "Warm, tactile heritage craft aesthetic. Warm amber-gold grade, deep rich shadows, "
            "analog film grain, imperfect and found-feeling cinematography. "
            "Extreme close-up macro shot. A single copper wire is being bent slowly between two "
            "bare, mature hands — the hands of someone in their 40s-60s with real work history: "
            "slightly calloused, capable, unhurried, no nail polish or jewelry. The wire fills "
            "two-thirds of the frame; fingertips rest at the edges. Grain is visible on the "
            "copper surface. Fingerprint impressions press into the metal as the wire resists "
            "the slow, deliberate bend. Camera is absolutely static — no movement whatsoever. "
            "Low, slightly angled framing — wire at center frame. "
            "Soft natural window light from frame-left, low morning sun, not direct. Diffused, "
            "warm, slightly hazy — as if through old glass. Pre-dawn quiet mood: still, "
            "intentional, contemplative. "
            "Background: worn wooden worktable surface so close that only warm amber grain and "
            "deep walnut tones are visible. Soft bokeh on the wood grain. "
            "Extremely shallow depth of field — the wire in crisp focus, everything else falls "
            "off rapidly. "
            "Color palette: copper amber, warm cream, deep walnut brown. "
            "Color grade: rich, warm, slightly desaturated, pulled toward amber, high local "
            "contrast on the wire surface. "
            "No music, no voiceover. Complete silence except the faint metallic sound of bending wire."
        ),
    },

    # ── Scene 2: The Workshop ─────────────────────────────────────────────────
    {
        "scene_id": "scene_2",
        "title": "Scene 2 — The Workshop (interior)",
        "source_duration": 10,
        "veo3_duration": "8s",
        "is_sub_scene": False,
        "stitch_group": None,
        "reference_image_url": "https://cdn.shopify.com/s/files/1/0269/9558/9223/products/Attitude-Gratitude-Charm-Bangle-Gold-Front-A21EBWAP8RG.jpg",
        "prompt": (
            "Warm, tactile heritage craft aesthetic. Warm amber-gold grade, deep rich shadows, "
            "analog film grain. "
            "Very slow, deliberate dolly pull-back — unhurried — beginning from close and "
            "revealing the full interior of a working artisan studio in New England. "
            "A craftsperson with mature, capable hands (40s-60s) works at a long worktable. "
            "On their wrist they wear a slender expandable gold-tone wire bangle with a single "
            "affirmation charm — the Attitude of Gratitude Charm Bangle in warm Rafaelian gold — "
            "worn naturally, never presented toward camera. "
            "Eye-level wide shot. Craftsperson centered at the worktable, tall factory windows "
            "behind them. "
            "Low-angle morning sun rakes through tall paned factory windows, casting hard-edged "
            "golden-hour quality light across the worktable surface. Purposeful, grounded, "
            "early-day stillness mood. "
            "Background: warm brick walls, timber beams, tall paned windows, natural studio "
            "clutter of a working workshop. "
            "Medium depth of field — craftsperson sharp, background slightly soft but readable. "
            "Color palette: warm amber, faded brick red, aged timber, cream. "
            "Color grade: warmer push in shadows, highlights pulled slightly golden, analog grain. "
            "Lower-third text overlay: 'Cranston, Rhode Island. 2004.' in small warm-gold serif "
            "typeface. Voiceover: 'There was a question she kept asking.'"
        ),
    },

    # ── Scene 3: The Question ─────────────────────────────────────────────────
    {
        "scene_id": "scene_3",
        "title": "Scene 3 — The Question",
        "source_duration": 12,
        "veo3_duration": "8s",
        "is_sub_scene": False,
        "stitch_group": None,
        "reference_image_url": "https://cdn.shopify.com/s/files/1/0269/9558/9223/products/Attitude-Gratitude-Charm-Bangle-Gold-Front-A21EBWAP8RG.jpg",
        "prompt": (
            "Warm, tactile heritage craft aesthetic. Warm amber-gold grade, analog film grain. "
            "Medium close-up of a woman aged 35-50, face left-of-center with natural headroom. "
            "She is reading a small meaning card — the kind of affirmation card that accompanies "
            "charm jewelry. Her expression is unguarded, private, not performing for the camera. "
            "As she reads, her expression shifts subtly — quiet recognition. Warm skin tones, "
            "natural hair, no heavy makeup. "
            "Camera is static with micro-reframe drift — as if handheld but deeply settled. "
            "Soft window light from one side, gentle wrap, strong cheekbone shadow. Diffused, "
            "intimate quality — like candlelight without flicker. Private, interior, absorbed mood. "
            "Background: soft, indistinct warm tones — studio or domestic setting. "
            "Shallow depth of field on face, background falls off. "
            "Color palette: skin tones, warm ivory, copper, faded gold. "
            "Color grade: gentle warmth, slight shadow lift, soft overall. "
            "Cut to overhead flat-lay: completely static overhead shot, camera directly above "
            "the worktable filling frame edge to edge. Objects arranged naturally, not staged: "
            "copper wire, small meaning cards, expandable gold-tone charm bangles — including a "
            "slender burnished-gold wire bangle with a single affirmation charm (Attitude of "
            "Gratitude style). Even depth of field — all objects sharp. Slightly cooler grade "
            "than the face shot to ground the still life. "
            "Voiceover: 'What if a piece of jewelry could carry something real? Not just gold. "
            "Not just silver. Something you would actually feel.'"
        ),
    },

    # ── Scene 4a through 4e: 22 Years montage ────────────────────────────────
    {
        "scene_id": "scene_4a",
        "title": "Scene 4a — 22 Years: Warm Kitchen",
        "source_duration": 3,
        "veo3_duration": "4s",
        "is_sub_scene": True,
        "stitch_group": "scene_4",
        "reference_image_url": "https://www.alexandani.com/cdn/shop/files/token-of-love-charm-bangle-1-AO250034RSG.jpg",
        "prompt": (
            "Warm, tactile heritage craft aesthetic. Analog film grain. Observational, "
            "naturalistic cinematography — loose handheld that follows action organically, "
            "no stabilization. "
            "A woman in her late 30s in a warm, sunlit kitchen. Only her wrists and hands are "
            "the primary focus — she is reaching for a morning mug of coffee. Her wrist carries "
            "stacked expandable wire bangles, including a slender gold-tone bangle with a single "
            "love-themed charm (Token of Love Charm Bangle, warm gold, compact charm flush "
            "against the wire). The bangles catch the warm kitchen window light mid-motion. "
            "The bangle is never held toward camera — it is incidental to the gesture. "
            "She is not looking at camera. Engaged in her own morning moment. "
            "Natural angle — varied and observational, not matching previous cut. "
            "Warm kitchen window light, amber and alive. "
            "Medium depth of field — enough context to feel real, shallow enough the bangles "
            "have intimacy. "
            "Color palette: warm kitchen amber. Color grade: warm shadow base, location "
            "temperature retained. "
            "Voiceover: '22 years.'"
        ),
    },
    {
        "scene_id": "scene_4b",
        "title": "Scene 4b — 22 Years: Car Window",
        "source_duration": 3,
        "veo3_duration": "4s",
        "is_sub_scene": True,
        "stitch_group": "scene_4",
        "reference_image_url": "https://www.alexandani.com/cdn/shop/files/glass-butterfly-beaded-charm-bracelet-1-AO251061WSS.jpg",
        "prompt": (
            "Warm, tactile heritage craft aesthetic. Analog film grain. Observational, "
            "naturalistic cinematography — loose handheld, no stabilization. "
            "A woman in her 50s leaning her arm out of a car window. Only her wrist and hand "
            "visible primarily. Stacked expandable wire bangles on her wrist, including a beaded "
            "silver-tone bangle with a glass butterfly centerpiece charm — semi-translucent "
            "glass butterfly wings catch the passing sunlight (Glass Butterfly Beaded Charm "
            "Bangle). The bangle is incidental — never presented toward camera. "
            "She is not looking at camera. Wind in the air, the feeling of being in motion. "
            "Natural angle from inside the car — cool car-window sidelight, warm ambient. "
            "Medium depth of field. "
            "Color palette: cool car window blue, warm ambient. "
            "Color grade: cool window light, warm shadow base. "
            "Voiceover: 'Across 66 countries.'"
        ),
    },
    {
        "scene_id": "scene_4c",
        "title": "Scene 4c — 22 Years: Garden",
        "source_duration": 4,
        "veo3_duration": "4s",
        "is_sub_scene": True,
        "stitch_group": "scene_4",
        "reference_image_url": "https://www.alexandani.com/cdn/shop/files/glass-butterfly-beaded-charm-bracelet-1-AO251061WSS.jpg",
        "prompt": (
            "Warm, tactile heritage craft aesthetic. Analog film grain. Observational, "
            "naturalistic cinematography — loose handheld, no stabilization. "
            "A woman in her 60s kneeling in a garden, hands in soil. Only wrists and hands "
            "primary. Stacked expandable wire bangles on her wrist — worn naturally, incidental "
            "to the gardening gesture. The bangles catch green-gold garden light mid-movement. "
            "She is not looking at camera. Absorbed in the work. "
            "Natural angle — slightly different from previous cuts. Overcast garden light, "
            "soft and diffused, green-gold quality. "
            "Medium depth of field. "
            "Color palette: garden green-gold, earthy tones. "
            "Color grade: cool overcast top light, warm shadow base. "
            "Voiceover: 'In 19 languages.'"
        ),
    },
    {
        "scene_id": "scene_4d",
        "title": "Scene 4d — 22 Years: Desk Workspace",
        "source_duration": 3,
        "veo3_duration": "4s",
        "is_sub_scene": True,
        "stitch_group": "scene_4",
        "reference_image_url": "https://www.alexandani.com/cdn/shop/files/token-of-love-charm-bangle-1-AO250034RSG.jpg",
        "prompt": (
            "Warm, tactile heritage craft aesthetic. Analog film grain. Observational, "
            "naturalistic cinematography — loose handheld, no stabilization. "
            "A woman in her late 20s at a desk, typing. Only her wrists and hands primary. "
            "Stacked expandable wire bangles on her wrist, incidental to typing gesture. "
            "Bangles catch soft desk-lamp light. She is not looking at camera. "
            "Natural angle — different from previous cuts. Soft desk-lamp light, warm and "
            "intimate, office neutral quality. "
            "Medium depth of field. "
            "Color palette: soft office neutral, warm lamp amber. "
            "Color grade: warm desk lamp, neutral mid-tones, warm shadow base. "
            "No voiceover in this sub-clip."
        ),
    },
    {
        "scene_id": "scene_4e",
        "title": "Scene 4e — 22 Years: Morning Café",
        "source_duration": 5,
        "veo3_duration": "4s",
        "is_sub_scene": True,
        "stitch_group": "scene_4",
        "reference_image_url": "https://www.alexandani.com/cdn/shop/files/token-of-love-charm-bangle-1-AO250034RSG.jpg",
        "prompt": (
            "Warm, tactile heritage craft aesthetic. Analog film grain. Observational, "
            "naturalistic cinematography — loose handheld, no stabilization. "
            "A woman in her 40s in a morning café, lifting a coffee cup. Only her wrist and "
            "hand primary. Stacked expandable wire bangles on her wrist — incidental, never "
            "presented. Bangles catch soft morning café light mid-lift. She is not looking at "
            "camera. Absorbed in her own moment. "
            "Natural angle — different from all previous cuts. Morning café ambient light, "
            "warm cream and amber quality. "
            "Medium depth of field. "
            "Color palette: café cream, warm amber morning light. "
            "Color grade: warm morning café quality, warm shadow base. "
            "No voiceover in this sub-clip."
        ),
    },

    # ── Scene 5: Light Through the Wire ──────────────────────────────────────
    {
        "scene_id": "scene_5",
        "title": "Scene 5 — Light Through the Wire",
        "source_duration": 12,
        "veo3_duration": "8s",
        "is_sub_scene": False,
        "stitch_group": None,
        "reference_image_url": "https://www.alexandani.com/cdn/shop/files/glass-butterfly-beaded-charm-bracelet-1-AO251061WSS.jpg",
        "prompt": (
            "Warm, tactile heritage craft aesthetic. Warm amber-gold grade, deep rich shadows, "
            "analog film grain. "
            "Medium close-up of a craftsperson's mature hand (40s-60s, calloused, capable, "
            "no nail polish) slowly raising a beaded silver-tone wire bangle up toward a tall "
            "factory window. The bangle features multiple small silver beads along the wire and "
            "a prominent glass butterfly centerpiece charm — the butterfly wings are "
            "semi-translucent glass (Glass Butterfly Beaded Charm Bangle). As the bangle rises "
            "to the window light, the semi-translucent glass butterfly beads catch the direct "
            "morning sun and scatter prismatic point-source light reflections across the warm "
            "amber grain of the worktable surface below. Camera holds on the light scatter "
            "across the wood for two full seconds — wonder, quiet revelation. "
            "Slightly low angle — hand in frame below the window's light source. Light scatter "
            "falls on worktable. Slow, barely perceptible push toward the light scatter — "
            "feels like leaning in. Hand and bangle in upper half of frame; refracted light "
            "points across the worktable surface below. "
            "Direct morning window light used as backlight through the glass butterfly beads. "
            "Hard source through semi-translucent glass — creates point-source reflections "
            "scattering across the wood. Wonder, quiet revelation mood. "
            "Background: tall factory window with morning sky beyond — overexposed white. "
            "Worktable surface below, warm amber grain. "
            "Split depth of field — bangle slightly soft, light scatter on worktable in crisp "
            "focus. "
            "Color palette: white window wash, warm amber wood, scattered prismatic light "
            "points, copper and silver tones. "
            "Color grade: highlights intentionally blow on the window. Warm, slightly lifted "
            "shadows on the wood surface. "
            "No lens flares, no added glow — physically plausible light scatter only. "
            "Voiceover: 'She just wanted to make something that meant something.'"
        ),
    },

    # ── Scene 6a through 6c: It Still Does ───────────────────────────────────
    {
        "scene_id": "scene_6a",
        "title": "Scene 6a — It Still Does: First Wrist (overhead)",
        "source_duration": 3,
        "veo3_duration": "4s",
        "is_sub_scene": True,
        "stitch_group": "scene_6",
        "reference_image_url": "https://www.alexandani.com/cdn/shop/files/lady-bug-opening-charm-bangle-1-AO260175SPSG.jpg",
        "prompt": (
            "Warm, tactile heritage craft aesthetic. Analog film grain. Slightly cooled from "
            "previous scenes — more neutral, grounding. Shadows kept warm. "
            "Intimate close-up of a wrist and hand from directly above. A woman approximately "
            "28 years old, in a domestic environment. She glances down at her wrist. Enough "
            "context to feel human — not a product shot. Her wrist carries stacked expandable "
            "wire bangles; one prominent bangle features a dimensional ladybug charm — red with "
            "black spots, opening mechanism, sitting three-dimensionally on a shiny gold-tone "
            "wire (Make Your Own Luck Ladybug Charm Bangle). The bangle is visible but she is "
            "the subject, not the bangle. She is not looking at camera. "
            "Camera completely static. Soft window ambient light. Gentle, intimate, not studio. "
            "Feels observed rather than lit. Quiet, settled mood. "
            "Shallow depth of field — wrist sharp, background falls away into warm blur. "
            "Color palette: skin tones, warm gold, soft ambient domestic background. "
            "Color grade: neutral with warm shadow base. "
            "Voiceover: 'It still does.'"
        ),
    },
    {
        "scene_id": "scene_6b",
        "title": "Scene 6b — It Still Does: Second Wrist (straight on)",
        "source_duration": 3,
        "veo3_duration": "4s",
        "is_sub_scene": True,
        "stitch_group": "scene_6",
        "reference_image_url": None,  # generic stacked bangles, no specific product
        "prompt": (
            "Warm, tactile heritage craft aesthetic. Analog film grain. Neutral grade, "
            "warm shadows. "
            "Intimate close-up of a wrist and hand, camera straight on at wrist level. "
            "A woman approximately 45 years old, in her own personal environment. She adjusts "
            "one of her stacked expandable wire bangles — a minor, habitual gesture, not "
            "performed. Stacked gold and silver-tone wire bangles on her wrist. She is not "
            "looking at camera. "
            "Very slight drift of camera — barely perceptible. Soft ambient indoor light. "
            "Gentle, intimate feel — observed, not lit. Quiet, settled mood. "
            "Shallow depth of field — wrist sharp, background a warm blur. "
            "Color palette: skin tones, gold, silver, warm ambient. "
            "Color grade: neutral with warm shadow base. "
            "No voiceover in this sub-clip."
        ),
    },
    {
        "scene_id": "scene_6c",
        "title": "Scene 6c — It Still Does: Third Wrist (slight low angle)",
        "source_duration": 4,
        "veo3_duration": "4s",
        "is_sub_scene": True,
        "stitch_group": "scene_6",
        "reference_image_url": None,  # generic stacked bangles, no specific product
        "prompt": (
            "Warm, tactile heritage craft aesthetic. Analog film grain. Neutral grade, "
            "warm shadows. Slow fade to black begins late in this clip. "
            "Intimate close-up of a wrist and hand resting in a lap, camera at a slight "
            "low angle looking up. A woman approximately 65 years old, in a settled domestic "
            "environment. She holds her wrist still in her lap. Stacked expandable wire bangles "
            "on her wrist — worn, personal. She is not looking at camera. "
            "Camera static, then a slow fade to black begins. Natural shade light, gentle, "
            "ambient. Quiet, settled mood — these women are not performing. "
            "Shallow depth of field — wrist sharp, background falls away. "
            "Color palette: skin tones, warm gold, silver, soft domestic background. "
            "Color grade: neutral with warm shadow base, fading to dark. "
            "No voiceover in this sub-clip."
        ),
    },

    # ── Scene 7: Est. 2004 ────────────────────────────────────────────────────
    {
        "scene_id": "scene_7",
        "title": "Scene 7 — Est. 2004",
        "source_duration": 5,
        "veo3_duration": "4s",
        "is_sub_scene": False,
        "stitch_group": None,
        "reference_image_url": None,  # brand card only, no product
        "prompt": (
            "Brand identity card. Warm, tactile heritage craft aesthetic. Densest analog film "
            "grain of the entire film. Complete stillness — no movement whatsoever. "
            "A dark, textured recycled copper metal surface fills the entire frame. The texture "
            "is deep, warm, almost tactile — aged copper undertones in a deep warm black field. "
            "Centered on this surface: the Alex and Ani logo in warm gold, and below it in "
            "small warm-gold serif typeface: 'Est. 2004'. Nothing else is in frame. No product. "
            "Camera is straight on, dead center, absolutely still for the full duration. "
            "Ambient light only — barely there. The surface itself provides depth. Flat and "
            "absorbed — the texture of recycled metal holds the light rather than reflecting. "
            "Complete quiet mood — a period at the end of a long sentence. "
            "Deep focus — entire surface in focus. The texture is the visual point. "
            "Color palette: deep warm black, aged copper undertones, warm gold lettering. "
            "Color grade: darkest grade of the film. Warm undertones in the blacks. "
            "Logo retains gold warmth. "
            "No voiceover. Complete silence. Text overlay: Alex and Ani logo centered in "
            "warm gold; 'Est. 2004' small, below, same gold. No animation on text."
        ),
    },
]

# ── Transition Notes ──────────────────────────────────────────────────────────
# Scene 1 → Scene 2: HARD CUT (only hard cut in the film per post-production notes)
# Scene 2 → Scene 3: DISSOLVE (slow breath between workshop reveal and intimate face)
# Scene 3 → Scene 4 (montage): DISSOLVE (from overhead still life into living motion)
# Scene 4 sub-clips: HARD CUTS between 4a/4b/4c/4d/4e (rhythm-driven montage)
# Scene 4 → Scene 5: DISSOLVE (from motion into stillness of the light reveal)
# Scene 5 → Scene 6: DISSOLVE (emotional transition from craft to wearer)
# Scene 6 sub-clips: DISSOLVE between 6a → 6b → 6c (6c fades to black)
# Scene 6c → Scene 7: FADE FROM BLACK (brand card emerges from silence)
# Scene 7: No transition — end of film.

# ── Helpers ───────────────────────────────────────────────────────────────────

def make_output_dir(base_dir: str) -> Path:
    """Create timestamped output directory and return the Path."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(base_dir) / timestamp
    out.mkdir(parents=True, exist_ok=True)
    return out


def download_file(url: str, dest_path: Path) -> bool:
    """Download a file from URL to dest_path. Returns True on success."""
    try:
        resp = requests.get(url, stream=True, timeout=120)
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as exc:
        print(f"    [WARN] Download failed: {exc}")
        return False


def generate_scene(scene: dict, output_dir: Path, retries: int, dry_run: bool) -> dict:
    """
    Call fal-ai/veo3-1 text-to-video for a single scene dict.
    Returns a result dict with keys: scene_id, title, status, output_path, error.
    When a reference_image_url is present on the scene, it is passed as image_url
    in the API arguments to ground the generation on the product reference.
    """
    scene_id = scene["scene_id"]
    title = scene["title"]
    prompt = scene["prompt"]
    duration = scene["veo3_duration"]
    ref_image_url = scene.get("reference_image_url")

    print(f"\n{'='*70}")
    print(f"  Generating: {title}")
    print(f"  Scene ID  : {scene_id}")
    print(f"  Duration  : {duration} (source: {scene['source_duration']}s)")
    print(f"  Endpoint  : {MODEL_ENDPOINT}")
    print(f"  Ref Image : {ref_image_url if ref_image_url else 'None'}")
    print(f"{'='*70}")
    print(f"  PROMPT PREVIEW (first 300 chars):")
    print(f"  {prompt[:300]}...")
    print()

    result = {
        "scene_id": scene_id,
        "title": title,
        "status": "skipped",
        "output_path": None,
        "error": None,
    }

    if dry_run:
        print("  [DRY RUN] Skipping API call.")
        result["status"] = "dry_run"
        return result

    arguments = {
        "prompt": prompt,
        "aspect_ratio": ASPECT_RATIO,
        "duration": duration,
        "negative_prompt": NEGATIVE_PROMPTS,
        "generate_audio": False,
    }
    if ref_image_url:
        arguments["image_url"] = ref_image_url

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            print(f"  Attempt {attempt}/{retries} — submitting to fal-ai/veo3-1 ...")
            start = time.time()

            def on_queue_update(update):
                if hasattr(update, "logs") and update.logs:
                    for log in update.logs:
                        msg = log.get("message", "") if isinstance(log, dict) else str(log)
                        if msg:
                            print(f"    [fal] {msg}")

            api_result = fal_client.subscribe(
                MODEL_ENDPOINT,
                arguments=arguments,
                with_logs=True,
                on_queue_update=on_queue_update,
            )

            elapsed = time.time() - start
            print(f"  API call completed in {elapsed:.1f}s")

            # Extract video URL from result
            video_url = None
            if isinstance(api_result, dict):
                # Common response shapes from fal.ai veo3-1
                if "video" in api_result:
                    v = api_result["video"]
                    if isinstance(v, dict):
                        video_url = v.get("url") or v.get("video_url")
                    elif isinstance(v, str):
                        video_url = v
                elif "video_url" in api_result:
                    video_url = api_result["video_url"]
                elif "output" in api_result:
                    out = api_result["output"]
                    if isinstance(out, dict):
                        video_url = out.get("url") or out.get("video_url")
                    elif isinstance(out, str):
                        video_url = out

            if not video_url:
                raise ValueError(
                    f"No video URL found in API response. Keys: {list(api_result.keys()) if isinstance(api_result, dict) else type(api_result)}"
                )

            print(f"  Video URL : {video_url}")

            # Download the video
            out_filename = f"{scene_id}.mp4"
            out_path = output_dir / out_filename
            print(f"  Downloading to: {out_path}")
            success = download_file(video_url, out_path)

            if success:
                print(f"  [OK] Saved: {out_path}")
                result["status"] = "success"
                result["output_path"] = str(out_path)
                return result
            else:
                raise IOError("Failed to download video file from URL.")

        except Exception as exc:
            last_error = exc
            print(f"  [ERROR] Attempt {attempt} failed: {exc}")
            if attempt < retries:
                wait = 5 * attempt
                print(f"  Retrying in {wait}s ...")
                time.sleep(wait)

    result["status"] = "failed"
    result["error"] = str(last_error)
    print(f"  [FAIL] All {retries} attempts failed for {scene_id}.")
    return result


# ── Main ──────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate Heritage Craft Origin video clips via fal-ai/veo3-1."
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Base output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--scenes",
        default=None,
        help=(
            "Comma-separated scene IDs to generate "
            "(e.g. scene_1,scene_4a,scene_7). Default: all scenes."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompts and config without making API calls.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Number of retry attempts per scene (default: 3).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Check FAL_KEY
    if not args.dry_run and not os.environ.get("FAL_KEY"):
        print("ERROR: FAL_KEY environment variable is not set.")
        print("  Export your key: export FAL_KEY=your_fal_api_key")
        sys.exit(1)

    # Filter scenes if requested
    scenes_to_run = SCENES
    if args.scenes:
        requested = {s.strip() for s in args.scenes.split(",")}
        scenes_to_run = [s for s in SCENES if s["scene_id"] in requested]
        if not scenes_to_run:
            print(f"ERROR: No matching scenes for filter: {args.scenes}")
            print(f"Available scene IDs: {[s['scene_id'] for s in SCENES]}")
            sys.exit(1)

    # Create output directory
    output_dir = make_output_dir(args.output_dir)
    print(f"\n{CONCEPT_TITLE} — {VARIATION_NAME}")
    print(f"Model    : {MODEL_ENDPOINT}")
    print(f"Scenes   : {len(scenes_to_run)} clips to generate")
    print(f"Output   : {output_dir}")
    print(f"Dry run  : {args.dry_run}")
    print(f"Retries  : {args.retries}")

    # Save a manifest of scene config for reference
    manifest_path = output_dir / "scene_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(
            [
                {
                    "scene_id": s["scene_id"],
                    "title": s["title"],
                    "source_duration": s["source_duration"],
                    "veo3_duration": s["veo3_duration"],
                    "is_sub_scene": s["is_sub_scene"],
                    "stitch_group": s["stitch_group"],
                    "reference_image_url": s.get("reference_image_url"),
                    "prompt_length": len(s["prompt"]),
                }
                for s in scenes_to_run
            ],
            f,
            indent=2,
        )
    print(f"\nScene manifest saved: {manifest_path}")

    # Generate each scene
    results = []
    for scene in scenes_to_run:
        result = generate_scene(
            scene=scene,
            output_dir=output_dir,
            retries=args.retries,
            dry_run=args.dry_run,
        )
        results.append(result)
        # Brief pause between API calls to avoid rate limiting
        if not args.dry_run and scene != scenes_to_run[-1]:
            time.sleep(2)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("  GENERATION SUMMARY")
    print(f"{'='*70}")

    succeeded = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "failed"]
    skipped = [r for r in results if r["status"] in ("dry_run", "skipped")]

    print(f"  Total scenes : {len(results)}")
    print(f"  Succeeded    : {len(succeeded)}")
    print(f"  Failed       : {len(failed)}")
    print(f"  Dry run/skip : {len(skipped)}")
    print()

    if succeeded:
        print("  Generated clips:")
        for r in succeeded:
            print(f"    [OK]  {r['scene_id']:20s}  {r['output_path']}")

    if failed:
        print("\n  Failed clips:")
        for r in failed:
            print(f"    [ERR] {r['scene_id']:20s}  {r['error']}")

    if skipped:
        print("\n  Skipped (dry run):")
        for r in skipped:
            print(f"    [--]  {r['scene_id']}")

    # Save full results JSON
    results_path = output_dir / "generation_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Full results saved: {results_path}")
    print(f"  Output directory  : {output_dir}")
    print()

    # Exit with non-zero if any failures
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()


# ══════════════════════════════════════════════════════════════════════════════
#  POST-PRODUCTION STITCHING NOTES
#  (from production guide — for editor reference, not executed by this script)
# ══════════════════════════════════════════════════════════════════════════════
#
#  SCENE ORDER & CLIP FILENAMES (in assembly order):
#    1.  scene_1.mp4          — The Wire (3s)
#    2.  scene_2.mp4          — The Workshop interior pull-back (10s)
#    3.  scene_3.mp4          — The Question: face + overhead flat-lay (12s)
#    4a. scene_4a.mp4         — 22 Years: Warm Kitchen (3s)
#    4b. scene_4b.mp4         — 22 Years: Car Window (3s)
#    4c. scene_4c.mp4         — 22 Years: Garden (4s)
#    4d. scene_4d.mp4         — 22 Years: Desk Workspace (3s)
#    4e. scene_4e.mp4         — 22 Years: Morning Café (5s)
#    5.  scene_5.mp4          — Light Through the Wire (12s)
#    6a. scene_6a.mp4         — It Still Does: Wrist 1, overhead (3s)
#    6b. scene_6b.mp4         — It Still Does: Wrist 2, straight on (3s)
#    6c. scene_6c.mp4         — It Still Does: Wrist 3, low angle, fades to black (4s)
#    7.  scene_7.mp4          — Est. 2004 brand card (5s)
#
#  TRANSITIONS:
#    scene_1 → scene_2  : HARD CUT — the ONLY hard cut in the film
#    scene_2 → scene_3  : DISSOLVE (1.0s) — from workshop reveal to intimate face
#    scene_3 → scene_4a : DISSOLVE (1.0s) — from overhead still life into living motion
#    scene_4a → 4b      : HARD CUT (rhythm-driven montage)
#    scene_4b → 4c      : HARD CUT (rhythm-driven montage)
#    scene_4c → 4d      : HARD CUT (rhythm-driven montage)
#    scene_4d → 4e      : HARD CUT (rhythm-driven montage)
#    scene_4e → scene_5 : DISSOLVE (1.5s) — from motion into stillness of light reveal
#    scene_5 → scene_6a : DISSOLVE (1.0s) — craft to wearer, emotional transition
#    scene_6a → 6b      : DISSOLVE (0.75s)
#    scene_6b → 6c      : DISSOLVE (0.75s) — 6c itself fades to black in final seconds
#    scene_6c → scene_7 : FADE FROM BLACK — brand card emerges from silence
#    scene_7            : END — hold full duration, no out transition
#
#  COLOR GRADE PASS:
#    Base LUT: Pull toward warm amber with rich, textured shadows throughout.
#    scene_7 receives the densest application — darkest grade, warmest shadow undertones.
#    scene_6 sub-clips: slightly cooler than scene_5 — more neutral, grounding emotion.
#    Overhead flat-lay in scene_3: cooler by one stop relative to the face shot.
#
#  GRAIN:
#    Apply analog film grain at moderate intensity, consistent across all scenes.
#    scene_7: densest grain of the entire film.
#    Do NOT clean up or reduce grain — all imperfection is intentional.
#
#  MUSIC MIX (guide reference):
#    scene_1 : Complete silence. Only faint metallic wire-bend sound design.
#    scene_2 : Single acoustic guitar fingerpick — one note, tentative. Enters so softly
#              a first-time viewer might not register it.
#    scene_3 : Single melodic guitar phrase — three to four notes, resolving softly.
#    scene_4 : Second acoustic guitar layer enters almost imperceptibly — counter-melody,
#              fingerpicked, soft.
#    scene_5 : Guitar sustains — single chord held, not resolved.
#    scene_6 : Guitar fades to a single held note — barely there. One breath of sound.
#    scene_7 : ABSOLUTE SILENCE.
#
#  VOICEOVER ASSEMBLY (guide reference):
#    scene_2 : "There was a question she kept asking."
#    scene_3 : "What if a piece of jewelry could carry something real?
#               Not just gold. Not just silver. Something you'd actually feel."
#    scene_4 : "22 years. Across 66 countries. In 19 languages."
#    scene_5 : "She just wanted to make something that meant something."
#    scene_6 : "It still does."
#    Voice: Female, warm, unhurried — mid-register, no vocal fry, no performance affect.
#
#  TEXT OVERLAYS:
#    scene_2 exterior cut: "Cranston, Rhode Island. 2004." — lower third,
#                          small light-weight serif, warm gold, fade in on exterior cut.
#    scene_7: Alex and Ani logo centered in warm gold. "Est. 2004" small, below, same gold.
#             No animation. No white text anywhere in the film.
#
#  SCENE 5 LIGHT SCATTER NOTE:
#    Keep physically plausible — no added lens flares, no post glow.
#    The prismatic scatter should read as optical refraction, not VFX.
#
#  SCENE 4 MONTAGE ASSEMBLY:
#    The five sub-clips (4a–4e) together should total approximately 18 seconds.
#    Trim or extend individual clips as needed during assembly to match the rhythm
#    of the voiceover "22 years. Across 66 countries. In 19 languages."
#
#  SCENE 6 ASSEMBLY NOTE:
#    The three sub-clips (6a–6c) together should total approximately 10 seconds.
#    scene_6c's fade to black should complete before scene_7 fades up from black.
#
#  TOTAL ASSEMBLED DURATION TARGET: ~70 seconds
#
# ══════════════════════════════════════════════════════════════════════════════
