import argparse
import csv
import json
import logging
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lib.tools import flatten_section_tags

TOOLS_JSON = os.path.join(PROJECT_ROOT, "docs", "tools.json")
DEFAULT_OUTPUT = os.path.join(PROJECT_ROOT, "docs", "tags.csv")
LOG_FILE = os.path.join(PROJECT_ROOT, "docs", "extract_tags.log")

TAG_PATTERN = re.compile(r"#(\w+)")

log = logging.getLogger("extract_tags")


def setup_logging(log_file: str = LOG_FILE) -> None:
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    log.addHandler(file_handler)
    log.addHandler(console_handler)


def load_section_map(tools_json: str = TOOLS_JSON) -> dict:
    log.debug(f"Loading section map from: {tools_json}")
    with open(tools_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    section_map = {}
    for section, value in data.items():
        tags = flatten_section_tags(value)
        for tag in tags:
            section_map[tag] = section
        log.debug(f"Section '{section}' mapped {len(tags)} tags")
    return section_map


def load_section_hints(tools_json: str = TOOLS_JSON) -> dict:
    log.debug(f"Loading section hints from: {tools_json}")
    with open(tools_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    hints = {}
    for section, value in data.items():
        hint_list = []
        for tag in flatten_section_tags(value):
            hint_list.append(tag)
            hint_list.extend(tag.split(" "))
        hints[section] = hint_list
        log.debug(f"Section '{section}' has {len(hint_list)} hints")
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
    log.debug(f"Scanning for markdown files under: {base_path}")
    matches = []
    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if d not in (".git", ".venv", "__pycache__", ".pytest_cache")]
        for file in files:
            if file.endswith(".md"):
                matches.append(os.path.join(root, file))
        if files or root == base_path:
            log.debug(f"Walked directory: {root} ({len(files)} files, {len(dirs)} subdirs)")
    log.debug(f"Found {len(matches)} markdown files")
    return matches


def extract_tags(markdown_files: list) -> dict:
    tags = {}
    for file_path in markdown_files:
        log.debug(f"Reading file: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        matches = TAG_PATTERN.findall(content)
        log.debug(f"Found {len(matches)} tag matches in {os.path.basename(file_path)}")
        for match in matches:
            tags.setdefault(match, 0)
            tags[match] += 1
    return tags


def write_tags_csv(tags: dict, section_map: dict, section_hints: dict, output_path: str) -> None:
    log.debug(f"Writing CSV to: {output_path}")
    rows = 0
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="|")
        writer.writerow(["tag", "suggested_section"])
        for tag in sorted(tags.keys()):
            section = suggest_section(tag, section_map, section_hints)
            log.debug(f"Tag '{tag}' -> suggested section '{section}'")
            writer.writerow([tag, section])
            rows += 1
    log.info(f"Wrote {rows} rows to {output_path}")


def show_review_popup(output_path: str) -> None:
    import ctypes

    message = f"A file is ready to be reviewed:\n{output_path}"
    log.debug("Showing review popup")
    ctypes.windll.user32.MessageBoxW(0, message, "Review Ready", 0x40)


def main(markdown_folder_path: str = PROJECT_ROOT, output_path: str = DEFAULT_OUTPUT, log_file: str = LOG_FILE) -> None:
    setup_logging(log_file)
    log.info("==== extract_tags run started ====")
    log.info(f"Target folder: {markdown_folder_path}")
    log.info(f"Output file: {output_path}")

    markdown_files = find_markdown_files(markdown_folder_path)
    tags = extract_tags(markdown_files)
    section_map = load_section_map()
    section_hints = load_section_hints()
    write_tags_csv(tags, section_map, section_hints, output_path)
    log.info(f"Found {len(tags)} unique tags across {len(markdown_files)} markdown files.")
    log.info(f"CSV written to {output_path}")
    show_review_popup(output_path)
    log.info("==== extract_tags run finished ====")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract #tags from markdown files into a CSV.")
    parser.add_argument("--markdown-folder-path", default=PROJECT_ROOT, help="Directory to scan for .md files")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output CSV path")
    parser.add_argument("--log-file", default=LOG_FILE, help="Path to log file")
    args = parser.parse_args()
    main(markdown_folder_path=args.markdown_folder_path, output_path=args.output, log_file=args.log_file)