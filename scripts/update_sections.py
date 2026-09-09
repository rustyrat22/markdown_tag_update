import argparse
import json
import logging
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
TOOLS_JSON = os.path.join(PROJECT_ROOT, "docs", "tools.json")
LOG_FILE = os.path.join(PROJECT_ROOT, "docs", "update_sections.log")

log = logging.getLogger("update_sections")


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
    log.debug(f"Loaded {len(data)} sections")
    return data


def save_tools(data: dict, tools_json: str = TOOLS_JSON) -> None:
    log.debug(f"Saving tools to: {tools_json}")
    with open(tools_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def is_dict_section(value) -> bool:
    return isinstance(value, dict)


def collect_section_tags(value) -> list:
    if is_dict_section(value):
        return [tag for sub in value.values() for tag in sub]
    return list(value)


def add_section(data: dict, name: str) -> bool:
    name = name.strip()
    if name in data:
        log.info(f"Section '{name}' already exists, skipping")
        return False
    data[name] = []
    log.info(f"Added new section '{name}'")
    return True


def add_sub_section(data: dict, section: str, sub_name: str) -> bool:
    section = section.strip()
    sub_name = sub_name.strip()
    if section not in data:
        log.warning(f"Section '{section}' does not exist")
        return False
    if not is_dict_section(data[section]):
        existing_tags = list(data[section])
        data[section] = {}
        if existing_tags:
            log.debug(f"Converted section '{section}' tags into default sub-section")
        data[section].setdefault("_default", existing_tags)
    if sub_name in data[section]:
        log.info(f"Sub-section '{section}/{sub_name}' already exists, skipping")
        return False
    data[section][sub_name] = []
    log.info(f"Added new sub-section '{section}/{sub_name}'")
    return True


def add_tag(data: dict, section: str, tag: str, sub_name: str = None) -> bool:
    section = section.strip()
    tag = tag.strip()
    if not tag:
        log.warning("Tag cannot be empty")
        return False
    if section not in data:
        log.warning(f"Section '{section}' does not exist")
        return False
    target_section = data[section]
    if sub_name:
        sub_name = sub_name.strip()
        if not is_dict_section(target_section):
            target_section = {"_default": list(target_section)}
            data[section] = target_section
            log.debug(f"Converted section '{section}' to sub-section structure")
        if sub_name not in target_section:
            target_section[sub_name] = []
            log.info(f"Created sub-section '{section}/{sub_name}' on the fly")
        target_list = target_section[sub_name]
    else:
        if is_dict_section(target_section):
            log.warning(f"Section '{section}' has sub-sections; provide --sub-section")
            return False
        target_list = data[section]
    if tag in target_list:
        log.info(f"Tag '{tag}' already in '{section}'")
        return False
    target_list.append(tag)
    log.info(f"Added tag '{tag}' to '{section}'")
    return True


def rebuild_tools(data: dict) -> dict:
    rebuilt = {}
    for section, value in data.items():
        if is_dict_section(value):
            sub_sections = {}
            for sub_name, tags in value.items():
                unique_tags = []
                seen = set()
                for tag in tags:
                    if tag not in seen:
                        seen.add(tag)
                        unique_tags.append(tag)
                sub_sections[sub_name] = unique_tags
            rebuilt[section] = sub_sections
            log.debug(f"Rebuilt section '{section}' with {len(sub_sections)} sub-sections")
        elif isinstance(value, list):
            unique_tags = []
            seen = set()
            for tag in value:
                if tag not in seen:
                    seen.add(tag)
                    unique_tags.append(tag)
            rebuilt[section] = unique_tags
            log.debug(f"Rebuilt section '{section}' with {len(unique_tags)} tags")
        else:
            log.warning(f"Skipping unsupported value type for section '{section}': {type(value).__name__}")
            rebuilt[section] = value
    return rebuilt


def main(tools_json: str = TOOLS_JSON, log_file: str = LOG_FILE, add_section_name: str = None,
         add_sub_section_args: tuple = None, add_tag_args: tuple = None, sub_name: str = None,
         rebuild: bool = False) -> None:
    setup_logging(log_file)
    log.info("==== update_sections run started ====")
    log.info(f"Tools file: {tools_json}")

    data = load_tools(tools_json)
    changed = 0

    if add_section_name:
        if add_section(data, add_section_name):
            changed += 1

    if add_sub_section_args:
        section, sub_name_arg = add_sub_section_args[0], add_sub_section_args[1]
        if add_sub_section(data, section, sub_name_arg):
            changed += 1

    if add_tag_args:
        section, tag = add_tag_args[0], add_tag_args[1]
        if add_tag(data, section, tag, sub_name):
            changed += 1

    if rebuild:
        data = rebuild_tools(data)
        changed += 1
        log.info("Rebuilt tools.json")

    if changed:
        save_tools(data, tools_json)
        log.info(f"Saved changes to {tools_json}")

    if not add_section_name and not add_sub_section and not add_tag_args and not rebuild:
        log.info("No operation requested. Use --add-section, --add-sub-section, --add-tag, and/or --rebuild.")

    total_sections = len(data)
    log.info(f"tools.json now has {total_sections} sections; {changed} change(s) applied.")
    log.info("==== update_sections run finished ====")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add sections/sub-sections/tags to docs/tools.json and rebuild it.")
    parser.add_argument("--add-section", help="Add a new top-level section")
    parser.add_argument("--add-sub-section", nargs=2, metavar=("SECTION", "SUB_SECTION"),
                        help="Add a sub-section to an existing section")
    parser.add_argument("--add-tag", nargs="+", metavar=("SECTION", "TAG"),
                        help="Add a tag to a section (optionally with --sub-section)")
    parser.add_argument("--sub-section", help="Sub-section to receive the tag (requires --add-tag)")
    parser.add_argument("--rebuild", action="store_true",
                        help="Rebuild the JSON file, deduplicating tags and normalizing sub-sections")
    parser.add_argument("--tools-json", default=TOOLS_JSON, help="Path to tools.json file")
    parser.add_argument("--log-file", default=LOG_FILE, help="Path to log file")
    args = parser.parse_args()

    main(
        tools_json=args.tools_json,
        log_file=args.log_file,
        add_section_name=args.add_section,
        add_sub_section_args=tuple(args.add_sub_section) if args.add_sub_section else None,
        add_tag_args=tuple(args.add_tag) if args.add_tag else None,
        sub_name=args.sub_section,
        rebuild=args.rebuild,
    )