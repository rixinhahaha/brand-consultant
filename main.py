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

from agents.brand_consultant import ALL_AGENTS, BRAND_CONSULTANT_PROMPT

PROJECT_DIR = Path(__file__).resolve().parent
SESSIONS_DIR = PROJECT_DIR / "sessions"


def print_banner() -> None:
    print("\n\033[1;97m" + "=" * 60)
    print("   AD CONTENT GENERATOR — Multi-Agent (Claude Agent SDK)")
    print("=" * 60 + "\033[0m")
    print("  Brand research → Ad audit → Competitor analysis → Concepts → Production prompts\n")


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
    SESSIONS_DIR.mkdir(exist_ok=True)

    print_banner()

    brand_url = input("  \033[1mBrand URL:\033[0m ").strip()
    if not brand_url:
        print("  Please provide a brand URL.")
        sys.exit(1)

    campaign_intent = input("  \033[1mCampaign intent\033[0m (optional): ").strip()

    depth_input = input("  \033[1mResearch depth\033[0m [light / medium / heavy] (default: medium): ").strip().lower()
    depth_map = {"l": "light", "m": "medium", "h": "heavy", "light": "light", "medium": "medium", "heavy": "heavy"}
    research_depth = depth_map.get(depth_input, "medium")

    initial_prompt = f"Analyze this brand and create an ad content playbook: {brand_url}"
    if campaign_intent:
        initial_prompt += f"\n\nCampaign intent: {campaign_intent}"
    initial_prompt += f"\n\nResearch depth: {research_depth}"

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
                print("\n  \033[92mSession ended. Check sessions/ for your ad concepts and production prompts.\033[0m\n")
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
