import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_JSON = os.path.join(ROOT, "docs", "tools.json")


def load_tools() -> dict:
    with open(TOOLS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def test_json_has_expected_sections():
    data = load_tools()
    expected = {"coding_languages", "applications", "libraries_or_modules", "miscellaneous"}
    assert set(data.keys()) >= expected


def test_no_duplicates_in_sections():
    data = load_tools()
    for section, items in data.items():
        assert len(items) == len(set(items)), f"Duplicates found in section: {section}"