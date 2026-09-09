def flatten_section_tags(section_value) -> list:
    if isinstance(section_value, dict):
        return [tag for sub_tags in section_value.values() for tag in sub_tags]
    return list(section_value)


def section_has_sub_sections(section_value) -> bool:
    return isinstance(section_value, dict)