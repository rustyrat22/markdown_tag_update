import argparse
import json
import logging
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
TOOLS_JSON = os.path.join(PROJECT_ROOT, "docs", "tools.json")
LOG_FILE = os.path.join(PROJECT_ROOT, "docs", "apply_tags.log")
PROJECT_ROOT_MD = PROJECT_ROOT

CODING_LANGUAGES_SECTION = "coding_languages"

log = logging.getLogger("apply_tags")


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


def load_tools(tools_json: str = TOOLS_JSON) -> dict:
    log.debug(f"Loading tools from: {tools_json}")
    with open(tools_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    for section, tags in data.items():
        log.debug(f"Loaded section '{section}' with {len(tags)} tags")
    return data


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


def find_headings(content: str) -> str:
    headings = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") and stripped != "## Tags":
            headings.append(stripped)
    log.debug(f"Found {len(headings)} headings")
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
                source = "content" if section == CODING_LANGUAGES_SECTION else "headings"
                log.debug(f"Detected tag '{tag}' in {source} (section: {section})")
                matched.add(tag)
    return sorted(matched)


def tags_section_header(content: str):
    for line in content.splitlines():
        stripped = line.strip()
        if re.match(r"^#{1,6}\s*[Tt]ags\s*$", stripped):
            return stripped
    return None


def append_missing_tags(content: str, tags: list) -> str:
    existing = [tag for tag in tags if re.search(r"(?<!\w)#" + re.escape(tag) + r"(?!\w)", content)]
    missing = [tag for tag in tags if tag not in existing]
    for tag in existing:
        log.debug(f"Tag '#{tag}' already present, skipping")
    if not missing:
        return content

    lines = content.rstrip("\n").splitlines()
    header = tags_section_header(content)
    if header is not None:
        log.debug(f"Found existing tags section header: '{header}'")
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
        log.debug(f"Inserted {len(missing)} tags into existing section at line {insert_at + 1}")
        return "\n".join(lines) + "\n"

    section = ["", "## Tags"] + ["#" + tag for tag in missing]
    log.debug(f"Appending new '## Tags' section with {len(missing)} tags")
    return "\n".join(lines) + "\n" + "\n".join(section) + "\n"


def add_tags_to_file(file_path: str, tools: dict) -> tuple:
    log.debug(f"Processing file: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    log.debug(f"Read {len(content)} characters / {content.count(chr(10)) + 1} lines from {os.path.basename(file_path)}")
    tags = collect_tags(content, tools)
    previous = content
    updated = append_missing_tags(content, tags)
    added_count = len(tags) - sum(1 for tag in tags if re.search(r"(?<!\w)#" + re.escape(tag) + r"(?!\w)", previous))
    if updated != content:
        added_chars = len(updated) - len(content)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated)
        log.info(f"Updated {os.path.basename(file_path)}: added tags {', '.join('#' + t for t in tags)} (+{added_chars} chars)")
        return True, added_count
    log.debug(f"No changes for {os.path.basename(file_path)}")
    return False, 0


def main(markdown_folder_path: str = PROJECT_ROOT_MD, tools_json: str = TOOLS_JSON, log_file: str = LOG_FILE) -> None:
    setup_logging(log_file)
    log.info("==== apply_tags run started ====")
    log.info(f"Target folder: {markdown_folder_path}")
    log.info(f"Tools file: {tools_json}")

    tools = load_tools(tools_json)
    markdown_files = find_markdown_files(markdown_folder_path)

    files_modified = 0
    tags_added_total = 0
    for file_path in markdown_files:
        modified, added_count = add_tags_to_file(file_path, tools)
        if modified:
            files_modified += 1
            tags_added_total += added_count

    log.info(f"Processed {len(markdown_files)} markdown files, {files_modified} modified, {tags_added_total} tags added.")
    log.info("==== apply_tags run finished ====")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add tags from tools.json to markdown files.")
    parser.add_argument("--markdown-folder-path", default=PROJECT_ROOT_MD, help="Directory to scan for .md files")
    parser.add_argument("--tools-json", default=TOOLS_JSON, help="Path to tools.json file")
    parser.add_argument("--log-file", default=LOG_FILE, help="Path to log file")
    args = parser.parse_args()
    main(markdown_folder_path=args.markdown_folder_path, tools_json=args.tools_json, log_file=args.log_file)