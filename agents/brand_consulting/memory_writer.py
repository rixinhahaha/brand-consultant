"""
Memory Writer agent — takes raw or structured data and writes schema-compliant memory files.

Schemas are auto-generated from the Pydantic models in models.py so they
never drift out of sync.
"""

import json

from claude_agent_sdk import AgentDefinition

from models import (
    BrandAdAuditMemory,
    BrandMemory,
    CategoryMemoryFile,
    CompetitorMemoryEntry,
    StoredAdConcept,
)

_MODELS = {
    "BrandMemory": BrandMemory,
    "BrandAdAuditMemory": BrandAdAuditMemory,
    "CompetitorMemoryEntry": CompetitorMemoryEntry,
    "CategoryMemoryFile": CategoryMemoryFile,
    "StoredAdConcept": StoredAdConcept,
}

_SCHEMA_BLOCK = "\n\n".join(
    f"### {name}\n```json\n{json.dumps(model.model_json_schema(), indent=2)}\n```"
    for name, model in _MODELS.items()
)

MEMORY_WRITER_AGENT = AgentDefinition(
    description=(
        "Writes schema-compliant memory JSON files. Accepts raw or structured "
        "analysis data from any agent, maps it to the correct Pydantic model, "
        "and writes the validated JSON to disk."
    ),
    prompt=f"""\
You are a Memory Writer agent. Your job is to take raw or structured data and
write it as valid JSON that conforms to a Pydantic schema.

## Workflow

1. The orchestrator provides: **schema name**, **file path**, and **data**.
2. Match every field to the schema definition below — use only the field names
   and types declared in the schema.
3. Write the JSON file using the Write tool.

## Schemas (auto-generated from models.py)

{_SCHEMA_BLOCK}

## Rules

- Output must pass `Model.model_validate_json()` for the target schema.
- Use the exact field names and types from the schema. Do not add, rename, or
  omit required fields.
- Where the schema declares `str`, write a single string — not a nested object.
- Where the schema declares `list[str]`, write a flat string array — not an
  array of objects.
- Infer missing required fields from context. Use null or empty defaults for
  missing optional fields.
- Write exactly one file per invocation.
""",
    tools=["Write", "Read"],
    model="haiku",
)
