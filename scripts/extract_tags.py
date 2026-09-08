import argparse
import csv
import json
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
TOOLS_JSON = os.path.join(PROJECT_ROOT, "docs", "tools.json")
DEFAULT_OUTPUT = os.path.join(PROJECT_ROOT, "docs", "tags.csv")

TAG_PATTERN = re.compile(r"#(\w+)")


def load_section_map(tools_json: str = TOOLS_JSON) -> dict:
    with open(tools_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    section_map = {}
    for section, tags in data.items():
        for tag in tags:
            section_map[tag] = section
    return section_map


def load_section_hints(tools_json: str = TOOLS_JSON) -> dict:
    with open(tools_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    hints = {}
    for section, tags in data.items():
        hint_list = []
        for tag in tags:
            hint_list.append(tag)
            hint_list.extend(tag.split(" "))
        hints[section] = hint_list
    return hints


def suggest_section(tag: str, section_map: dict, section_hints: dict) -> str:
    if tag in section_map:
        return section_map[tag]
    lower = tag.lower()
    for section, hints in section_hints.items():
        if any(hint in lower for hint in hints):
            return section
    return "miscellaneous"


def find_markdown_files(base_path: str) -> list:
    matches = []
    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if d not in (".git", ".venv", "__pycache__", ".pytest_cache")]
        for file in files:
            if file.endswith(".md"):
                matches.append(os.path.join(root, file))
    return matches


def extract_tags(markdown_files: list) -> dict:
    tags = {}
    for file_path in markdown_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        for match in TAG_PATTERN.findall(content):
            tags.setdefault(match, 0)
            tags[match] += 1
    return tags


def write_tags_csv(tags: dict, section_map: dict, section_hints: dict, output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="|")
        writer.writerow(["tag", "suggested_section"])
        for tag in sorted(tags.keys()):
            writer.writerow([tag, suggest_section(tag, section_map, section_hints)])


def show_review_popup(output_path: str) -> None:
    import ctypes

    message = f"A file is ready to be reviewed:\n{output_path}"
    ctypes.windll.user32.MessageBoxW(0, message, "Review Ready", 0x40)


def main(markdown_folder_path: str = PROJECT_ROOT, output_path: str = DEFAULT_OUTPUT) -> None:
    markdown_files = find_markdown_files(markdown_folder_path)
    tags = extract_tags(markdown_files)
    section_map = load_section_map()
    section_hints = load_section_hints()
    write_tags_csv(tags, section_map, section_hints, output_path)
    print(f"Found {len(tags)} unique tags across {len(markdown_files)} markdown files.")
    print(f"Written to {output_path}")
    show_review_popup(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract #tags from markdown files into a CSV.")
    parser.add_argument("--markdown-folder-path", default=PROJECT_ROOT, help="Directory to scan for .md files")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output CSV path")
    args = parser.parse_args()
    main(markdown_folder_path=args.markdown_folder_path, output_path=args.output)