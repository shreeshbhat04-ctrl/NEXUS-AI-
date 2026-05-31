import json
from typing import Any


def extract_mcp_payload(result: Any) -> Any:
    if getattr(result, "structuredContent", None) is not None:
        return result.structuredContent

    content = getattr(result, "content", None) or []
    if not content:
        return None

    first = content[0]
    text = getattr(first, "text", None)
    if text is None:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text
