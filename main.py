"""
Multi-Agent Ad Content Generator — CLI Entry Point
===================================================
Uses ClaudeSDKClient for multi-turn conversation with a Brand Consultant
orchestrator that delegates to specialized subagents.

Usage:
    python main.py
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
)

# Patch parse_message to handle unknown message types (e.g. rate_limit_event)
# instead of raising MessageParseError, which kills the entire async generator chain.
import claude_agent_sdk._internal.message_parser as _msg_parser

_original_parse_message = _msg_parser.parse_message


def _lenient_parse_message(data: dict) -> object:
    try:
        return _original_parse_message(data)
    except Exception:
        # Convert unknown message types to SystemMessage so the stream stays alive
        return SystemMessage(subtype=data.get("type", "unknown"), data=data)


_msg_parser.parse_message = _lenient_parse_message

from agents.brand_consulting.brand_consultant import ALL_AGENTS, BRAND_CONSULTANT_PROMPT
from memory import slugify, load_brand_ad_audit, load_category_memory, list_known_brands, list_brand_concepts

PROJECT_DIR = Path(__file__).resolve().parent


def print_banner() -> None:
    print("\n\033[1;97m" + "=" * 60)
    print("   AD CONTENT GENERATOR — Multi-Agent (Claude Agent SDK)")
    print("=" * 60 + "\033[0m")
    print("  Brand research → Ad audit → Competitor analysis → Concepts\n")


def print_message(text: str) -> None:
    """Print assistant text to the console."""
    print(f"\033[97m{text}\033[0m")


def print_tool_use(name: str, description: str) -> None:
    """Print a tool delegation event."""
    print(f"\n  \033[90m→ [{name}] {description}\033[0m")


def print_system_event(subtype: str, data: dict) -> None:
    """Print system events like agent delegation."""
    if subtype == "init":
        session_id = data.get("session_id", "unknown")
        print(f"  \033[90m  Session: {session_id}\033[0m")


async def run() -> None:
    print_banner()

    # ── Smart onboarding: show existing brands or onboard new ──
    known_brands = list_known_brands()
    brand_url = ""
    brand_slug = ""
    brand_memory = None
    brand_ad_audit = None
    category_memory = None

    if known_brands:
        print("  \033[1mYour brands:\033[0m")
        for i, mem in enumerate(known_brands, 1):
            sessions_label = f" · {mem.category_slug}"
            print(f"    {i}. {mem.brand.name} ({mem.brand.category}){sessions_label} — last updated {mem.last_updated}")
        print(f"    {len(known_brands) + 1}. Onboard a new brand")
        print()

        choice = input("  \033[1mSelect a brand:\033[0m ").strip()

        selected_brand = None
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(known_brands):
                selected_brand = known_brands[idx - 1]
            elif idx == len(known_brands) + 1:
                pass  # fall through to new brand URL prompt
            else:
                print("  Invalid selection.")
                sys.exit(1)
        else:
            print("  Please make a selection.")
            sys.exit(1)

        if selected_brand:
            brand_slug = slugify(selected_brand.brand.name)
            brand_memory = selected_brand
            brand_ad_audit = load_brand_ad_audit(brand_slug)
            if brand_memory.category_slug:
                category_memory = load_category_memory(brand_memory.category_slug)
            print(f"\n  \033[92mLoaded {brand_memory.brand.name}\033[0m")

    if not brand_memory:
        brand_url = input("  \033[1mBrand URL:\033[0m ").strip()
        if not brand_url:
            print("  Please provide a brand URL.")
            sys.exit(1)

    if not brand_slug and brand_url:
        brand_slug = slugify(brand_url.rstrip("/").split("/")[-1].replace(".com", "").replace("www.", ""))

    campaign_intent = input("  \033[1mCampaign intent:\033[0m ").strip()
    if not campaign_intent:
        print("  Please provide a campaign intent (e.g., 'self-gifting ritual', 'summer launch').")
        sys.exit(1)

    # ── Load existing concepts from memory ──
    ad_concepts_dir = PROJECT_DIR / "memory" / "brands" / brand_slug / "ad_concepts"
    existing_concepts = list_brand_concepts(brand_slug)
    existing_concepts_summary = ""
    if existing_concepts:
        lines = []
        for c in existing_concepts:
            lines.append(f"- [{c.content_type}] \"{c.concept.title}\" ({c.concept.format}) — {c.campaign_intent} ({c.created_date})")
        existing_concepts_summary = "\n".join(lines)
        print(f"  \033[90mFound {len(existing_concepts)} existing concepts in library\033[0m")

    # ── Build initial prompt ──
    if brand_memory:
        initial_prompt = f"Create an ad content playbook for {brand_memory.brand.name}."
        initial_prompt += f"\n\nCampaign intent: {campaign_intent}"
        initial_prompt += f"\n\n## Existing Brand Memory (brand_slug: {brand_slug})\n"
        initial_prompt += brand_memory.model_dump_json(indent=2)

        if brand_ad_audit:
            initial_prompt += f"\n\n## Existing Ad Audit (last updated: {brand_ad_audit.last_updated})\n"
            initial_prompt += brand_ad_audit.model_dump_json(indent=2)

        if category_memory:
            initial_prompt += f"\n\n## Existing Category Memory (category_slug: {brand_memory.category_slug})\n"
            initial_prompt += category_memory.model_dump_json(indent=2)
    else:
        initial_prompt = f"Analyze this brand and create an ad content playbook: {brand_url}"
        initial_prompt += f"\n\nCampaign intent: {campaign_intent}"
        initial_prompt += "\n\nNo existing memory found for this brand. This is a fresh session."

    initial_prompt += f"\n\n## Ad Concepts Directory\n{ad_concepts_dir}"

    if existing_concepts_summary:
        initial_prompt += f"\n\n## Existing Concepts in Library ({len(existing_concepts)} concepts)\n{existing_concepts_summary}"
    else:
        initial_prompt += "\n\n## Existing Concepts in Library\nNo existing concepts found."

    def _stderr_handler(line: str) -> None:
        print(f"  \033[90m[cli] {line.rstrip()}\033[0m", file=sys.stderr)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("  \033[91mError: ANTHROPIC_API_KEY not found. Set it in .env or export it.\033[0m")
        sys.exit(1)
    print(f"  \033[90mAPI key: {api_key[:12]}...{api_key[-4:]}\033[0m")

    options = ClaudeAgentOptions(
        system_prompt=BRAND_CONSULTANT_PROMPT,
        allowed_tools=["Task", "Read", "Glob", "WebSearch", "WebFetch", "Write"],
        agents=ALL_AGENTS,
        permission_mode="acceptEdits",
        cwd=str(PROJECT_DIR),
        model="sonnet",
        stderr=_stderr_handler,
        env={"ANTHROPIC_API_KEY": api_key},
    )

    print("  \033[90mConnecting to Claude...\033[0m")
    async with ClaudeSDKClient(options=options) as client:
        print(f"\n\033[95m{'━' * 60}\033[0m")
        print(f"\033[1;95m  STARTING BRAND ANALYSIS\033[0m")
        print(f"\033[95m{'━' * 60}\033[0m\n")

        await client.query(initial_prompt)
        await _receive_and_display(client)

        # Multi-turn feedback loop
        while True:
            print()
            user_input = input("\033[1;96m  You:\033[0m ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                print(f"\n  \033[92mSession ended. Your concepts are in memory/brands/{brand_slug}/ad_concepts/.\033[0m")
                print(f"  \033[92mTo produce media, run: python media_production.py\033[0m\n")
                break

            await client.query(user_input)
            await _receive_and_display(client)


async def _receive_and_display(client: ClaudeSDKClient) -> None:
    """Iterate over response messages until ResultMessage."""
    async for message in client.receive_response():
        _display_message(message)


def _display_message(message: object) -> None:
    """Route a message to the appropriate display handler."""
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                print_message(block.text)
            elif isinstance(block, ToolUseBlock):
                desc = _tool_description(block.name, block.input)
                print_tool_use(block.name, desc)
    elif isinstance(message, SystemMessage):
        print_system_event(message.subtype, message.data)
    elif isinstance(message, ResultMessage):
        if message.is_error:
            print(f"\n  \033[91mError: {message.result}\033[0m")
        else:
            cost = f"${message.total_cost_usd:.4f}" if message.total_cost_usd else "N/A"
            print(f"\n  \033[90mCompleted in {message.duration_ms / 1000:.1f}s · "
                  f"Cost: {cost} · Turns: {message.num_turns}\033[0m")


def _tool_description(name: str, input_data: dict) -> str:
    """Generate a human-readable description of a tool call."""
    if name == "Task":
        agent = input_data.get("subagent_type", "")
        desc = input_data.get("description", "")
        return f"Delegating to {agent}: {desc}" if agent else desc
    if name == "Write":
        path = input_data.get("file_path", "")
        return f"Writing to {path}"
    if name == "WebSearch":
        query = input_data.get("query", "")
        return f"Searching: {query}"
    if name == "WebFetch":
        url = input_data.get("url", "")
        return f"Fetching: {url}"
    return str(input_data)[:100]


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n\n  Cancelled.")
    except Exception as e:
        print(f"\n  \033[91mError: {e}\033[0m")
        raise


if __name__ == "__main__":
    main()
