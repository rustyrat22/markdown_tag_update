import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "functions"))
from tag_manager import ensure_tag


@pytest.fixture
def tmp_json(tmp_path):
    path = os.path.join(tmp_path, "tools.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"applications": ["docker"]}, f)
    return path


def test_adds_tag_when_missing(tmp_json):
    added = ensure_tag("applications", "docker2", tmp_json)

    assert added is True
    with open(tmp_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "docker2" in data["applications"]
    assert "docker" in data["applications"]


def test_does_not_add_duplicate(tmp_json):
    added = ensure_tag("applications", "docker", tmp_json)

    assert added is False
    with open(tmp_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["applications"].count("docker") == 1


def test_creates_section_when_missing(tmp_json):
    added = ensure_tag("coding_languages", "rust", tmp_json)

    assert added is True
    with open(tmp_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["coding_languages"] == ["rust"]