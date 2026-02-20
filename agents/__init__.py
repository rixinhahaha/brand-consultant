"""
Agent definitions for the multi-agent ad content generator.
"""

from agents.brand_researcher import BRAND_RESEARCHER_AGENT
from agents.brand_ad_analyzer import BRAND_AD_ANALYZER_AGENT
from agents.competitor_ad_analyzer import COMPETITOR_AD_ANALYZER_AGENT
from agents.ad_concept_generator import AD_CONCEPT_GENERATOR_AGENT
from agents.video_prompt_generator import VIDEO_PROMPT_GENERATOR_AGENT
from agents.image_prompt_generator import IMAGE_PROMPT_GENERATOR_AGENT
from agents.brand_consultant import BRAND_CONSULTANT_PROMPT, ALL_AGENTS

__all__ = [
    "BRAND_RESEARCHER_AGENT",
    "BRAND_AD_ANALYZER_AGENT",
    "COMPETITOR_AD_ANALYZER_AGENT",
    "AD_CONCEPT_GENERATOR_AGENT",
    "VIDEO_PROMPT_GENERATOR_AGENT",
    "IMAGE_PROMPT_GENERATOR_AGENT",
    "BRAND_CONSULTANT_PROMPT",
    "ALL_AGENTS",
]
