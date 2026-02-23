"""
Media Production Pipeline — CLI Entry Point
============================================
Uses ClaudeSDKClient for multi-turn conversation with a Media Production
Director that generates production guides (.json), writes runnable fal.ai scripts,
and manages execution with a feedback loop.

Usage:
    python media_production.py
"""

import asyncio
import json
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
        return SystemMessage(subtype=data.get("type", "unknown"), data=data)


_msg_parser.parse_message = _lenient_parse_message

from agents.media_production import MEDIA_CONSULTANT_PROMPT, MEDIA_GENERATION_AGENTS
from memory import list_known_brands, slugify, get_ad_concepts_dir

PROJECT_DIR = Path(__file__).resolve().parent


def print_banner() -> None:
    print("\n\033[1;97m" + "=" * 60)
    print("   MEDIA PRODUCTION PIPELINE (Claude Agent SDK)")
    print("=" * 60 + "\033[0m")
    print("  Concepts → Production guides → fal.ai scripts → Execution\n")


def print_message(text: str) -> None:
    """Print assistant text to the console."""
    print(f"\033[97m{text}\033[0m")


def print_tool_use(name: str, description: str) -> None:
    """Print a tool use event."""
    print(f"\n  \033[90m→ [{name}] {description}\033[0m")


def print_system_event(subtype: str, data: dict) -> None:
    """Print system events like session initialization."""
    if subtype == "init":
        session_id = data.get("session_id", "unknown")
        print(f"  \033[90m  Session: {session_id}\033[0m")


def select_brand() -> tuple[str, dict | None, list[dict]]:
    """Let the user pick a brand from memory. Returns (brand_slug, brand_context_dict or None, products_list)."""
    known_brands = list_known_brands()
    if not known_brands:
        print("  \033[93mNo brands found in memory. Run `python main.py` first to onboard a brand.\033[0m")
        sys.exit(1)

    print("  \033[1mYour brands:\033[0m\n")
    for i, mem in enumerate(known_brands, 1):
        print(f"    {i}. {mem.brand.name} ({mem.brand.category}) — last updated {mem.last_updated}")

    print()
    while True:
        choice = input("  \033[1mSelect brand\033[0m (enter number): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(known_brands):
                brand = known_brands[idx]
                brand_slug = slugify(brand.brand.name)
                brand_context = {
                    "name": brand.brand.name,
                    "vibe": brand.brand.vibe,
                    "category": brand.brand.category,
                    "tone": brand.brand.tone,
                    "usp": brand.brand.usp,
                    "materials": brand.brand.materials,
                    "price_range": brand.brand.price_range,
                }
                products = [
                    {
                        "name": p.name,
                        "description": p.description,
                        "price": p.price,
                        "image_uri": p.image_uri,
                        "key_features": p.key_features,
                    }
                    for p in brand.products
                ]
                print(f"\n  \033[92mLoaded {brand.brand.name}\033[0m")
                return brand_slug, brand_context, products
        except ValueError:
            pass
        print("  Invalid selection. Try again.")


def enter_context() -> str:
    """Prompt for campaign context / additional notes."""
    print("\n  \033[1mCampaign context\033[0m\n")
    context = input("  \033[1mDescribe your campaign intent or additional context:\033[0m ").strip()
    if context:
        print(f"  \033[92mContext noted.\033[0m")
    else:
        print(f"  \033[90mNo additional context provided.\033[0m")
    return context


def select_products(products: list[dict]) -> list[dict]:
    """Let the user pick products from the brand catalogue to feature."""
    if not products:
        print("\n  \033[93mNo products in brand catalogue. Skipping product selection.\033[0m")
        return []

    print(f"\n  \033[1mProduct catalogue ({len(products)} products):\033[0m\n")
    for i, p in enumerate(products, 1):
        print(f"    {i}. {p['name']} — {p['price']}")
        print(f"       {p['description'][:80]}")

    print(f"\n  Enter product numbers (comma-separated), 'all', or press Enter to skip.")
    choice = input("  \033[1mSelect products:\033[0m ").strip()

    if not choice:
        print("  \033[90mNo products selected.\033[0m")
        return []
    if choice.lower() == "all":
        print(f"  \033[92mSelected all {len(products)} products.\033[0m")
        return products

    selected = []
    for part in choice.split(","):
        try:
            idx = int(part.strip()) - 1
            if 0 <= idx < len(products):
                selected.append(products[idx])
        except ValueError:
            pass

    if selected:
        print(f"  \033[92mSelected {len(selected)} product(s): {', '.join(p['name'] for p in selected)}\033[0m")
    else:
        print("  \033[93mNo valid products selected.\033[0m")
    return selected


def select_concept(ad_concepts_dir: Path) -> tuple[Path, dict]:
    """Discover concepts in ad_concepts_dir and let the user pick one interactively.

    Returns (concept_dir_path, concept_data_dict).
    """
    if not ad_concepts_dir.exists():
        print("  \033[91mError: No ad concepts found. Run `python main.py` first to generate concepts.\033[0m")
        sys.exit(1)

    concepts = []
    for concept_dir in sorted(ad_concepts_dir.iterdir()):
        concept_file = concept_dir / "concept.json"
        if concept_dir.is_dir() and concept_file.exists():
            try:
                data = json.loads(concept_file.read_text())
                concepts.append((concept_dir, data))
            except Exception:
                continue

    if not concepts:
        print("  \033[91mError: No valid concept.json files found in ad concepts directory.\033[0m")
        sys.exit(1)

    print(f"\n  \033[1mAvailable concepts ({len(concepts)}):\033[0m\n")
    for i, (cdir, cdata) in enumerate(concepts, 1):
        title = cdata.get("concept", {}).get("title", cdir.name)
        fmt = cdata.get("concept", {}).get("format", "?")
        campaign = cdata.get("campaign_intent", "")
        date = cdata.get("created_date", "")
        content_type = cdata.get("content_type", "")
        print(f"    {i}. [{content_type}] \"{title}\" ({fmt})")
        if campaign or date:
            print(f"       Campaign: {campaign} · Created: {date}")

    print()
    while True:
        choice = input("  \033[1mSelect concept\033[0m (enter number): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(concepts):
                concept_dir, concept_data = concepts[idx]
                title = concept_data.get("concept", {}).get("title", concept_dir.name)
                print(f"\n  \033[92mSelected: \"{title}\"\033[0m")
                return concept_dir, concept_data
        except ValueError:
            pass
        print("  Invalid selection. Try again.")


def load_all_concepts(ad_concepts_dir: Path) -> list[tuple[Path, dict]]:
    """Load all concept.json files from the ad concepts directory.

    Returns list of (concept_dir_path, concept_data_dict).
    """
    if not ad_concepts_dir.exists():
        return []

    concepts = []
    for concept_dir in sorted(ad_concepts_dir.iterdir()):
        concept_file = concept_dir / "concept.json"
        if concept_dir.is_dir() and concept_file.exists():
            try:
                data = json.loads(concept_file.read_text())
                concepts.append((concept_dir, data))
            except Exception:
                continue
    return concepts


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def discover_images(directory: str) -> list[str]:
    """Scan a directory for image files and return sorted absolute paths."""
    dir_path = Path(directory).resolve()
    if not dir_path.is_dir():
        print(f"  \033[93mWarning: '{directory}' is not a valid directory. Skipping.\033[0m")
        return []
    images = sorted(str(f) for f in dir_path.iterdir()
                    if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS)
    if not images:
        print(f"  \033[93mNo image files found in '{directory}'.\033[0m")
    else:
        print(f"  \033[92mFound {len(images)} image(s) in {dir_path.name}/\033[0m")
    return images


def collect_production_inputs() -> dict:
    """Collect optional product assets dir and character refs dir."""
    result = {"product_asset_images": [], "character_ref_images": []}
    print("\n  \033[1mOptional production inputs\033[0m (press Enter to skip any)\n")
    product_dir = input("  \033[1mProduct assets directory:\033[0m ").strip()
    if product_dir:
        result["product_asset_images"] = discover_images(product_dir)
    char_dir = input("  \033[1mCharacter references directory:\033[0m ").strip()
    if char_dir:
        result["character_ref_images"] = discover_images(char_dir)
    return result


async def run() -> None:
    print_banner()

    # Step 1: Select brand
    brand_slug, brand_context, products = select_brand()

    # Step 2: Select products to feature (before context — products inform the context question)
    selected_products = select_products(products)

    # Step 3: Campaign context
    campaign_context = enter_context()

    # Step 4: Load all concepts from ad_concepts directory
    ad_concepts_dir = get_ad_concepts_dir(brand_slug)
    all_concepts = load_all_concepts(ad_concepts_dir)
    if not all_concepts:
        print("  \033[91mError: No valid concepts found. Run `python main.py` first to generate concepts.\033[0m")
        sys.exit(1)
    print(f"\n  \033[92mLoaded {len(all_concepts)} concept(s) from {ad_concepts_dir}\033[0m")

    # Step 5: Collect optional asset inputs
    production_inputs = collect_production_inputs()

    # Build initial prompt with brand context, all products, selected products, all concepts
    brand_context_str = json.dumps(brand_context, indent=2) if brand_context else "No brand context available."

    initial_prompt = (
        f"## Brand Context\n"
        f"```json\n{brand_context_str}\n```\n\n"
    )

    # Full product catalogue
    if products:
        initial_prompt += "## Full Product Catalogue\n"
        for p in products:
            initial_prompt += f"- **{p['name']}** ({p['price']})\n"
            initial_prompt += f"  Description: {p['description']}\n"
            initial_prompt += f"  Image: {p['image_uri']}\n"
            initial_prompt += f"  Key features: {', '.join(p['key_features'])}\n\n"

    # Selected products (or none)
    if selected_products:
        initial_prompt += "## Selected Products\n"
        initial_prompt += "The user selected these products to feature in the production:\n\n"
        for p in selected_products:
            initial_prompt += f"- **{p['name']}** ({p['price']})\n"
            initial_prompt += f"  Description: {p['description']}\n"
            initial_prompt += f"  Image: {p['image_uri']}\n"
            initial_prompt += f"  Key features: {', '.join(p['key_features'])}\n\n"
        initial_prompt += (
            "Use the product image URIs above as product reference images when no explicit "
            "product asset directory was provided. These are web catalogue images from the brand's site.\n\n"
        )
    else:
        initial_prompt += (
            "## Selected Products\n"
            "No products selected — after concept selection, recommend the most suitable "
            "products from the full catalogue above.\n\n"
        )

    # All available concepts
    initial_prompt += f"## Ad Concepts Directory\n`{ad_concepts_dir}`\n\n"
    initial_prompt += f"## Available Concepts ({len(all_concepts)})\n"
    for concept_dir, concept_data in all_concepts:
        concept_json_str = json.dumps(concept_data, indent=2)
        initial_prompt += (
            f"### Concept directory: `{concept_dir}`\n"
            f"```json\n{concept_json_str}\n```\n\n"
        )

    if production_inputs["product_asset_images"]:
        initial_prompt += "## Product Asset Images\n"
        for img_path in production_inputs["product_asset_images"]:
            initial_prompt += f"- {img_path}\n"
        initial_prompt += "\n"

    if production_inputs["character_ref_images"]:
        initial_prompt += "## Character Reference Images\n"
        for img_path in production_inputs["character_ref_images"]:
            initial_prompt += f"- {img_path}\n"
        initial_prompt += "\n"

    if campaign_context:
        initial_prompt += f"## Campaign Context\n{campaign_context}\n\n"

    initial_prompt += (
        "Begin the production workflow. "
        "Start with Step 1: recommend the best concepts for the selected products and campaign context, "
        "or present all concepts for the user to choose from if no products were selected."
    )

    def _stderr_handler(line: str) -> None:
        print(f"  \033[90m[cli] {line.rstrip()}\033[0m", file=sys.stderr)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("  \033[91mError: ANTHROPIC_API_KEY not found. Set it in .env or export it.\033[0m")
        sys.exit(1)
    print(f"  \033[90mAPI key: {api_key[:12]}...{api_key[-4:]}\033[0m")

    options = ClaudeAgentOptions(
        system_prompt=MEDIA_CONSULTANT_PROMPT,
        allowed_tools=["Read", "Glob", "Write", "Task", "Bash"],
        agents=MEDIA_GENERATION_AGENTS,
        permission_mode="acceptEdits",
        cwd=str(PROJECT_DIR),
        model="sonnet",
        stderr=_stderr_handler,
        env={"ANTHROPIC_API_KEY": api_key},
    )

    print("  \033[90mConnecting to Claude...\033[0m")
    async with ClaudeSDKClient(options=options) as client:
        print(f"\n\033[95m{'━' * 60}\033[0m")
        print(f"\033[1;95m  MEDIA PRODUCTION PIPELINE\033[0m")
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
                print("\n  \033[92mSession ended. Check media_creation_scripts/ for your generation scripts.\033[0m\n")
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
    if name == "Write":
        path = input_data.get("file_path", "")
        return f"Writing to {path}"
    if name == "Read":
        path = input_data.get("file_path", "")
        return f"Reading {path}"
    if name == "Glob":
        pattern = input_data.get("pattern", "")
        return f"Searching: {pattern}"
    if name == "Task":
        agent = input_data.get("agent", input_data.get("subagent_type", ""))
        desc = input_data.get("description", "")
        return f"Delegating to {agent}: {desc}" if desc else f"Delegating to {agent}"
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
