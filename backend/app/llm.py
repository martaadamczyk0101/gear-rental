import json
import logging

import anthropic
from pydantic import BaseModel

from .config import ANTHROPIC_API_KEY, ANTHROPIC_SEARCH_MODEL

logger = logging.getLogger("booksy.llm")

SYSTEM_PROMPT = """You are a hardware-matching assistant for an internal company equipment \
rental tool.

You will be given a natural-language description of what someone needs and a JSON list of \
hardware items currently in inventory. Each item has:
- id
- name
- brand
- purchase_date (ISO YYYY-MM-DD, or null if not on file)
- notes (free text, may be null)
- status (available / in use / in repair)

Use every one of these fields when they're relevant to the request - including purchase_date for \
requests about age, purchase timing, or how old/new an item is (e.g. "bought before 2023",
"our oldest laptops", "anything purchased in the last year"), and notes for requests about \
condition or history. Also use general domain knowledge for requests that don't name a field \
directly - for example, "testing a mobile app" implies phones and tablets, and "a video call" \
implies a laptop, webcam, or headset.

Return the ids of every item that satisfies the request. Only return ids that actually appear in \
the provided list - never invent one. Return an empty list if nothing in the inventory is \
relevant."""


class HardwareMatch(BaseModel):
    matching_ids: list[int]


class SemanticSearchUnavailable(Exception):
    """Raised when a semantic search request cannot be completed."""


def find_matching_ids(query: str, inventory: list[dict]) -> list[int]:
    if not ANTHROPIC_API_KEY:
        raise SemanticSearchUnavailable("ANTHROPIC_API_KEY is not configured")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    try:
        response = client.messages.parse(
            model=ANTHROPIC_SEARCH_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Need: {query}\n\nInventory:\n{json.dumps(inventory)}",
                }
            ],
            output_format=HardwareMatch,
        )
    except anthropic.APIError as err:
        logger.error("Semantic search request failed: %s", err)
        raise SemanticSearchUnavailable("Semantic search request failed") from err

    if response.parsed_output is None:
        raise SemanticSearchUnavailable("Semantic search returned an unparseable response")

    return response.parsed_output.matching_ids
