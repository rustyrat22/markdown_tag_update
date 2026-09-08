import argparse
import json
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
TOOLS_JSON = os.path.join(PROJECT_ROOT, "docs", "tools.json")
PROJECT_ROOT_MD = PROJECT_ROOT

CODING_LANGUAGES_SECTION = "coding_languages"


def load_tools(tools_json: str = TOOLS_JSON) -> dict:
    with open(tools_json, "r", encoding="utf-8") as f:
        return json.load(f)


def find_markdown_files(base_path: str) -> list:
    matches = []
    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if d not in (".git", ".venv", "__pycache__", ".pytest_cache")]
        for file in files:
            if file.endswith(".md"):
                matches.append(os.path.join(root, file))
    return matches


def find_headings(content: str) -> str:
    headings = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") and stripped != "## Tags":
            headings.append(stripped)
    return "\n".join(headings)


def tag_matches(tag: str, text: str) -> bool:
    pattern = re.compile(r"(?<!\w)" + re.escape(tag) + r"(?!\w)", re.IGNORECASE)
    return pattern.search(text) is not None


def collect_tags(content: str, tools: dict) -> list:
    headings_text = find_headings(content)
    matched = set()
    for section, tags in tools.items():
        search_text = content if section == CODING_LANGUAGES_SECTION else headings_text
        for tag in tags:
            if tag_matches(tag, search_text):
                matched.add(tag)
    return sorted(matched)


def tags_section_header(content: str):
    for line in content.splitlines():
        stripped = line.strip()
        if re.match(r"^#{1,6}\s*[Tt]ags\s*$", stripped):
            return stripped
    return None


def append_missing_tags(content: str, tags: list) -> str:
    missing = [tag for tag in tags if not re.search(r"(?<!\w)#" + re.escape(tag) + r"(?!\w)", content)]
    if not missing:
        return content

    lines = content.rstrip("\n").splitlines()
    header = tags_section_header(content)
    if header is not None:
        insert_at = 0
        for i, line in enumerate(lines):
            if line.strip() == header:
                insert_at = i + 1
                break
        while insert_at < len(lines) and lines[insert_at].strip().startswith("#") and not lines[insert_at].strip().startswith("## Tags"):
            insert_at += 1
        new_tags = ["#" + tag for tag in missing]
        index = insert_at
        while index < len(lines) and lines[index].strip().startswith("#") and not lines[index].strip().startswith("##"):
            index += 1
        lines[insert_at:index] = new_tags + lines[insert_at:index]
        return "\n".join(lines) + "\n"

    section = ["", "## Tags"] + ["#" + tag for tag in missing]
    return "\n".join(lines) + "\n" + "\n".join(section) + "\n"


def add_tags_to_file(file_path: str, tools: dict) -> list:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    tags = collect_tags(content, tools)
    updated = append_missing_tags(content, tags)
    if updated != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated)
    return tags


def main(markdown_folder_path: str = PROJECT_ROOT_MD, tools_json: str = TOOLS_JSON) -> None:
    tools = load_tools(tools_json)
    markdown_files = find_markdown_files(markdown_folder_path)
    for file_path in markdown_files:
        tags = add_tags_to_file(file_path, tools)
        if tags:
            print(f"{os.path.basename(file_path)}: added tags -> {', '.join(tags)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add tags from tools.json to markdown files.")
    parser.add_argument("--markdown-folder-path", default=PROJECT_ROOT_MD, help="Directory to scan for .md files")
    parser.add_argument("--tools-json", default=TOOLS_JSON, help="Path to tools.json file")
    args = parser.parse_args()
    main(markdown_folder_path=args.markdown_folder_path, tools_json=args.tools_json)