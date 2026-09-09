# markdown_tag_update

A Python project for automatically scanning, extracting, and applying `#tags` to markdown files. It maintains a central tag registry (`docs/tools.json`) and can export tags to CSV for review before updating the registry.

## Project Structure

```
markdown_tag_update/
├── scripts/
│   ├── apply_tags.py        # Applies tags to markdown files
│   ├── extract_tags.py      # Extracts tags from markdown files into CSV
│   ├── update_tags_json.py  # Updates tools.json from a reviewed CSV
│   └── update_sections.py   # Adds sections/sub-sections/tags and rebuilds tools.json
├── functions/
│   └── tag_manager.py       # Utility to add a tag to tools.json
├── lib/
│   └── tools.py             # Shared helpers for handling tools.json sections
├── docs/
│   ├── tools.json           # Central tag registry
│   └── tags.csv             # Exported tags CSV
├── tests/
│   ├── test_tag_manager.py  # Tests for tag_manager
│   ├── test_tools_json.py   # Tests for tools.json structure
│   └── test_ensure_folder.py# Tests for ensure_folder utility
└── src/markdown_tag_update/ # Package entry point (stub)
```

## Scripts

### `apply_tags.py`

Scans all markdown files under a directory, detects tags by matching headings and content against `docs/tools.json`, and appends matching `#tags` to each file under a `## Tags` section.

**Parameters:**

| Parameter             | Default                        | Description                          |
|-----------------------|--------------------------------|--------------------------------------|
| `--markdown-folder-path` | Project root directory     | Directory to recursively scan for `.md` files |
| `--tools-json`           | `docs/tools.json`          | Path to the tag registry JSON file   |
| `--log-file`             | `docs/apply_tags.log`      | Path to write the log file           |

**Examples:**

```bash
# Apply tags using defaults (scans the project root)
python scripts/apply_tags.py

# Apply tags to a specific folder
python scripts/apply_tags.py --markdown-folder-path "C:\docs\my_notes"

# Use a custom tools.json and log file
python scripts/apply_tags.py --tools-json "C:\config\my_tags.json" --log-file "C:\logs\apply.log"
```

**Behavior:**

- For each `.md` file, headings are extracted and matched against tags in `tools.json` sections (except `coding_languages`).
- For the `coding_languages` section, the full file content is searched.
- Matched tags are appended under an existing `## Tags` header or a newly created one.
- Tags already present in the file (as `#tagname`) are skipped.
- A log file records all activity at DEBUG level; INFO is printed to the console.

---

### `extract_tags.py`

Scans all markdown files for `#tag` patterns, counts occurrences, suggests a section for each tag based on `tools.json`, and writes the results to a CSV file. A Windows popup notifies the user when the CSV is ready for review.

**Parameters:**

| Parameter             | Default                        | Description                          |
|-----------------------|--------------------------------|--------------------------------------|
| `--markdown-folder-path` | Project root directory     | Directory to recursively scan for `.md` files |
| `--output`               | `docs/tags.csv`            | Path for the output CSV file         |
| `--log-file`             | `docs/extract_tags.log`    | Path to write the log file           |

**Examples:**

```bash
# Extract tags using defaults
python scripts/extract_tags.py

# Extract tags from a different folder and write to a specific CSV
python scripts/extract_tags.py --markdown-folder-path "C:\docs\my_notes" --output "C:\output\tags.csv"
```

**CSV format** (pipe-delimited):

```
tag|suggested_section
docker|applications
python|coding_languages
```

---

### `update_tags_json.py`

Reads a reviewed `tags.csv` and merges approved tags into `docs/tools.json`. New sections are created automatically if needed.

**Parameters:**

| Parameter       | Default                | Description                          |
|-----------------|------------------------|--------------------------------------|
| `--csv-path`    | `docs/tags.csv`        | Path to the reviewed tags CSV file   |
| `--tools-json`  | `docs/tools.json`      | Path to the tag registry JSON file   |
| `--log-file`    | `docs/update_tags_json.log` | Path to write the log file      |

**Examples:**

```bash
# Update tools.json from the default CSV
python scripts/update_tags_json.py

# Use a specific CSV and tools.json
python scripts/update_tags_json.py --csv-path "C:\reviewed\tags.csv" --tools-json "C:\config\my_tags.json"
```

> Note: if a section already contains sub-sections, tags from the CSV are skipped for that section with a warning. Use `update_sections.py` to add tags to a specific sub-section instead.

---

### `update_sections.py`

Adds new sections, sub-sections, and tags directly to `docs/tools.json`, and can rebuild the file to normalize it (deducing duplicate tags and preserving sub-section structure). Sections can be a flat list of tags or a dict of sub-sections, e.g.:

```json
{
  "applications": {
    "_default": ["docker", "postgresql"],
    "database_servers": ["mysql"]
  },
  "coding_languages": ["powershell", "sql", "python"]
}
```

**Parameters:**

| Parameter          | Default                    | Description                                     |
|--------------------|----------------------------|-------------------------------------------------|
| `--add-section`    | —                          | Add a new top-level section                     |
| `--add-sub-section` | —                         | Add a sub-section to an existing section (takes `SECTION SUB_SECTION`) |
| `--add-tag`        | —                          | Add a tag to a section (takes `SECTION TAG`, optional `--sub-section`) |
| `--sub-section`    | —                          | Sub-section to receive the tag (used with `--add-tag`) |
| `--rebuild`        | `False`                    | Rebuild/normalize `tools.json` (dedupe tags, keep sub-section structure) |
| `--tools-json`     | `docs/tools.json`          | Path to the tag registry JSON file              |
| `--log-file`       | `docs/update_sections.log` | Path to write the log file                      |

**Examples:**

```bash
# Add a new top-level section
python scripts/update_sections.py --add-section cloud_platforms

# Add a sub-section (existing tags move under "_default")
python scripts/update_sections.py --add-sub-section applications database_servers

# Add a tag to an existing section
python scripts/update_sections.py --add-tag coding_languages rust

# Add a tag to a specific sub-section
python scripts/update_sections.py --add-tag applications mysql --sub-section database_servers

# Rebuild/normalize the file
python scripts/update_sections.py --rebuild

# Combine operations in one run
python scripts/update_sections.py --add-section cloud_platforms --add-tag cloud_platforms aws --rebuild
```

**Behavior:**

- `--add-section` creates an empty section if it does not exist.
- `--add-sub-section` converts a flat (list) section into a dict, placing existing tags under `_default`.
- `--add-tag` with `--sub-section` auto-creates the sub-section and the sub-section structure if needed.
- `--add-tag` without `--sub-section` requires the section to be a flat list.
- `--rebuild` rewrites the file with normalized formatting, removes duplicate tags, and keeps the sub-section hierarchy.

---

### `functions/tag_manager.py`

A utility module providing the `ensure_tag()` function for programmatic tag management.

**Function:** `ensure_tag(section, tag, tools_json=DEFAULT_TOOLS_JSON) -> bool`

| Parameter   | Type   | Description                                      |
|-------------|--------|--------------------------------------------------|
| `section`   | `str`  | The section name in `tools.json` (e.g. `applications`) |
| `tag`       | `str`  | The tag to add (e.g. `docker`)                   |
| `tools_json`| `str`  | Path to `tools.json` (defaults to `docs/tools.json`) |

Returns `True` if the tag was added; `False` if it already exists.

**Example:**

```python
from functions.tag_manager import ensure_tag

# Add "rust" to the coding_languages section
ensure_tag("coding_languages", "rust")

# Add a tag to a new section (creates it automatically)
ensure_tag("cloud_platforms", "aws")
```

---

## Libraries

| Library              | Version    | Purpose                                            |
|----------------------|------------|----------------------------------------------------|
| `markdown`           | >=3.10.3   | Markdown parsing                                   |
| `python-frontmatter` | >=1.3.0    | Front-matter parsing for markdown files            |
| `pyyaml`             | >=6.0.3    | YAML front-matter support                          |
| `pytest`             | >=9.1.1    | Test framework (dev dependency)                    |
| `ruff`               | >=0.16.6   | Linter and formatter (dev dependency)              |

**Standard library modules used across scripts:** `argparse`, `csv`, `json`, `logging`, `os`, `re`, `sys`, `ctypes` (Windows popup in `extract_tags.py`).

---

## Tests

All tests are located in the `tests/` directory and run via `pytest`.

### `test_tag_manager.py`

Tests for the `ensure_tag()` function in `functions/tag_manager.py`.

| Test                                  | Description                                      |
|---------------------------------------|--------------------------------------------------|
| `test_adds_tag_when_missing`          | Verifies a new tag is added to an existing section |
| `test_does_not_add_duplicate`         | Verifies duplicate tags are not added twice      |
| `test_creates_section_when_missing`   | Verifies a new section is created when it does not exist |

### `test_tools_json.py`

Tests for the structure and integrity of `docs/tools.json`.

| Test                                  | Description                                      |
|---------------------------------------|--------------------------------------------------|
| `test_json_has_expected_sections`     | Verifies `tools.json` contains the expected sections: `coding_languages`, `applications`, `libraries_or_modules`, `miscellaneous` |
| `test_no_duplicates_in_sections`      | Verifies no duplicate tags exist within any section |

### `test_ensure_folder.py`

Tests for an external `ensure_folder` utility (from a sibling project).

| Test                                  | Description                                      |
|---------------------------------------|--------------------------------------------------|
| `test_creates_folder_when_missing`    | Verifies a folder is created when it does not exist |
| `test_does_nothing_when_folder_exists`| Verifies existing folders are not modified       |
| `test_creates_nested_folder_path`     | Verifies nested directories are created correctly |

**Run tests:**

```bash
pytest
```

---

## License

See [LICENSE](LICENSE).
