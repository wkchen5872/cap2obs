"""Markdown frontmatter parsing and injection utilities for Cap2Obs tracking."""

import logging
import re
from pathlib import Path

_log = logging.getLogger(__name__)


# Cap2Obs tracking property keys
_PROP_SOURCE = "cap2obs_source"
_PROP_MANAGED = "cap2obs_managed"
_PROP_MANAGED_DATE = "cap2obs_managed_date"
_CAP2OBS_KEYS = (_PROP_SOURCE, _PROP_MANAGED, _PROP_MANAGED_DATE)

# Matches a YAML frontmatter block at the start of a file.
# The closing --- does NOT require a preceding newline so that empty blocks
# (---\n---\n) are handled correctly.
_FRONTMATTER_RE = re.compile(r"^---[ \t]*\r?\n(.*?)---[ \t]*\r?\n", re.DOTALL)


def parse_frontmatter(content: str) -> dict:
    """
    Extract cap2obs tracking properties from YAML frontmatter.

    Only reads cap2obs_source, cap2obs_managed, and cap2obs_managed_date.
    All other YAML keys are ignored.

    Args:
        content: Full markdown file content.

    Returns:
        Dict with zero to three keys present: cap2obs_source (str),
        cap2obs_managed (str), cap2obs_managed_date (str).
        Missing keys are absent from the result.
    """
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return {}

    result = {}
    for line in match.group(1).splitlines():
        for key in _CAP2OBS_KEYS:
            m = re.match(rf"^{key}:\s*(.*)", line)
            if m:
                raw = m.group(1).strip()
                # Strip surrounding quotes if present
                if len(raw) >= 2 and raw[0] in ('"', "'") and raw[-1] == raw[0]:
                    raw = raw[1:-1]
                result[key] = raw
                break

    return result


def inject_properties(
    content: str,
    source_id: str,
    managed: bool = False,
    managed_date: str = "",
) -> str:
    """
    Inject or update cap2obs tracking properties in markdown content.

    Inserts the three cap2obs keys without disturbing other YAML keys.
    If no frontmatter block exists, a new one is prepended.

    Args:
        content: Full markdown file content.
        source_id: Value for cap2obs_source (typically the file stem).
        managed: Value for cap2obs_managed.
        managed_date: Value for cap2obs_managed_date.

    Returns:
        Updated markdown content with cap2obs properties present.
    """
    cap2obs_lines = [
        f'{_PROP_SOURCE}: "{source_id}"',
        f"{_PROP_MANAGED}: {str(managed).lower()}",
        f"{_PROP_MANAGED_DATE}: {managed_date}",
    ]

    match = _FRONTMATTER_RE.match(content)

    if not match:
        new_block = "---\n" + "\n".join(cap2obs_lines) + "\n---\n"
        return new_block + content

    yaml_block = match.group(1)
    kept_lines = [
        line for line in yaml_block.splitlines()
        if not any(line.startswith(f"{k}:") for k in _CAP2OBS_KEYS)
    ]
    new_yaml = "\n".join(kept_lines + cap2obs_lines) if kept_lines else "\n".join(cap2obs_lines)
    return f"---\n{new_yaml}\n---\n{content[match.end():]}"


def scan_markdown_index(directory: Path) -> dict:
    """
    Scan a directory for .md files and build a cap2obs_source index.

    Only files that have a cap2obs_source YAML property are included.

    Args:
        directory: Root directory to scan recursively.

    Returns:
        Dict mapping cap2obs_source value → {"path": Path, "managed": bool}.
    """
    index: dict = {}

    if not directory.exists():
        return index

    for md_file in directory.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        props = parse_frontmatter(content)
        source_id = props.get(_PROP_SOURCE, "")
        if not source_id:
            continue

        managed_raw = props.get(_PROP_MANAGED, "false").lower().strip()
        managed = managed_raw in ("true", "yes", "1")
        if source_id in index:
            _log.warning(
                "Duplicate cap2obs_source '%s' in '%s' and '%s'; keeping first-seen.",
                source_id,
                index[source_id]["path"].name,
                md_file.name,
            )
            continue
        index[source_id] = {"path": md_file, "managed": managed}

    return index
