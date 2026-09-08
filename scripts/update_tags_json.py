import argparse
import csv
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
TOOLS_JSON = os.path.join(PROJECT_ROOT, "docs", "tools.json")
DEFAULT_CSV = os.path.join(PROJECT_ROOT, "docs", "tags.csv")


def load_tools(tools_json: str = TOOLS_JSON) -> dict:
    with open(tools_json, "r", encoding="utf-8") as f:
        return json.load(f)


def read_csv_records(csv_path: str) -> list:
    records = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            records.append(row)
    return records


def update_tools(records: list, tools_json: str = TOOLS_JSON) -> int:
    data = load_tools(tools_json)
    added = 0
    for record in records:
        tag = record.get("tag")
        section = record.get("suggested_section")
        if not tag or not section:
            continue
        section = section.strip()
        if section not in data:
            data[section] = []
        if tag not in data[section]:
            data[section].append(tag)
            added += 1
    with open(tools_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return added


def main(csv_path: str = DEFAULT_CSV, tools_json: str = TOOLS_JSON) -> None:
    records = read_csv_records(csv_path)
    added = update_tools(records, tools_json)
    print(f"Processed {len(records)} records. Added {added} new tags to {tools_json}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update docs/tools.json from a tags CSV.")
    parser.add_argument("--csv-path", default=DEFAULT_CSV, help="Path to tags CSV file")
    parser.add_argument("--tools-json", default=TOOLS_JSON, help="Path to tools.json file")
    args = parser.parse_args()
    main(csv_path=args.csv_path, tools_json=args.tools_json)