import json
import os

DEFAULT_TOOLS_JSON = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "tools.json"
)


def ensure_tag(section: str, tag: str, tools_json: str = DEFAULT_TOOLS_JSON) -> bool:
    with open(tools_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    if section not in data:
        data[section] = []

    if tag not in data[section]:
        data[section].append(tag)
        with open(tools_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True

    return False