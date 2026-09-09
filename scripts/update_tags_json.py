import argparse
import csv
import json
import logging
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lib.tools import section_has_sub_sections

TOOLS_JSON = os.path.join(PROJECT_ROOT, "docs", "tools.json")
DEFAULT_CSV = os.path.join(PROJECT_ROOT, "docs", "tags.csv")
LOG_FILE = os.path.join(PROJECT_ROOT, "docs", "update_tags_json.log")

log = logging.getLogger("update_tags_json")


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


def read_csv_records(csv_path: str) -> list:
    log.debug(f"Reading CSV from: {csv_path}")
    records = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            records.append(row)
    log.debug(f"Read {len(records)} records from CSV")
    return records


def update_tools(records: list, tools_json: str = TOOLS_JSON) -> int:
    data = load_tools(tools_json)
    added = 0
    for record in records:
        tag = record.get("tag")
        section = record.get("suggested_section")
        if not tag or not section:
            log.debug(f"Skipping record with missing fields: {record}")
            continue
        section = section.strip()
        log.debug(f"Processing record: tag='{tag}' section='{section}'")
        if section in data and section_has_sub_sections(data[section]):
            log.warning(f"Section '{section}' has sub-sections; skipping tag '{tag}'. Use scripts/update_sections.py to add tags to a specific sub-section.")
            continue
        if section not in data:
            log.debug(f"Creating new section '{section}'")
            data[section] = []
        if tag not in data[section]:
            data[section].append(tag)
            added += 1
            log.debug(f"Added tag '{tag}' to section '{section}'")
        else:
            log.debug(f"Tag '{tag}' already in section '{section}', skipping")
    with open(tools_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    log.debug(f"Wrote updated tools to: {tools_json}")
    return added


def main(csv_path: str = DEFAULT_CSV, tools_json: str = TOOLS_JSON, log_file: str = LOG_FILE) -> None:
    setup_logging(log_file)
    log.info("==== update_tags_json run started ====")
    log.info(f"CSV file: {csv_path}")
    log.info(f"Tools file: {tools_json}")

    records = read_csv_records(csv_path)
    added = update_tools(records, tools_json)
    log.info(f"Processed {len(records)} records. Added {added} new tags to {tools_json}.")
    log.info("==== update_tags_json run finished ====")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update docs/tools.json from a tags CSV.")
    parser.add_argument("--csv-path", default=DEFAULT_CSV, help="Path to tags CSV file")
    parser.add_argument("--tools-json", default=TOOLS_JSON, help="Path to tools.json file")
    parser.add_argument("--log-file", default=LOG_FILE, help="Path to log file")
    args = parser.parse_args()
    main(csv_path=args.csv_path, tools_json=args.tools_json, log_file=args.log_file)