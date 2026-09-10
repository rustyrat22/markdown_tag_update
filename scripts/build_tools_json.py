import argparse
import json
import logging
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
TOOLS_JSON = os.path.join(DOCS_DIR, "tools.json")
LOG_FILE = os.path.join(DOCS_DIR, "build_tools_json.log")

log = logging.getLogger("build_tools_json")


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


def read_lines(txt_path: str) -> list:
    log.debug(f"Reading lines from: {txt_path}")
    items = []
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            item = line.strip()
            if item:
                items.append(item)
    log.debug(f"Read {len(items)} items from {txt_path}")
    return items


def build_tools(docs_dir: str = DOCS_DIR) -> dict:
    sections = {
        "coding_languages": ["coding_languages.txt"],
        "applications": ["applications.txt"],
        "add_ons": ["libraries.txt", "modules.txt"],
        "miscellaneous": ["miscellaneous.txt"],
    }
    data = {}
    for section, filenames in sections.items():
        items = []
        for filename in filenames:
            items.extend(read_lines(os.path.join(docs_dir, filename)))
        data[section] = items
        log.debug(f"Section '{section}' has {len(items)} items")
    return data


def main(docs_dir: str = DOCS_DIR, tools_json: str = TOOLS_JSON, log_file: str = LOG_FILE) -> None:
    setup_logging(log_file)
    log.info("==== build_tools_json run started ====")
    log.info(f"Docs directory: {docs_dir}")
    log.info(f"Tools file: {tools_json}")

    data = build_tools(docs_dir)
    with open(tools_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    for section, tags in data.items():
        log.info(f"Section '{section}' has {len(tags)} tags")
    log.info(f"Wrote {len(data)} sections to {tools_json}.")
    log.info("==== build_tools_json run finished ====")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build docs/tools.json from text files.")
    parser.add_argument("--docs-dir", default=DOCS_DIR, help="Path to docs directory")
    parser.add_argument("--tools-json", default=TOOLS_JSON, help="Path to tools.json file")
    parser.add_argument("--log-file", default=LOG_FILE, help="Path to log file")
    args = parser.parse_args()
    main(docs_dir=args.docs_dir, tools_json=args.tools_json, log_file=args.log_file)