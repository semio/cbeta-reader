"""Build table of contents from mulu entries across all juan files."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .parser import parse_xml


@dataclass
class TocEntry:
    level: int
    text: str
    type: str
    juan: int
    anchor: str = ""
    children: list[TocEntry] = field(default_factory=list)


def build_toc(cbeta_path: Path, href: str) -> list[TocEntry]:
    """Build a full TOC for a text by scanning all its juan files.

    href should be like "XML/T/T01/T01n0001_001.xml".
    """
    xml_path = cbeta_path / href
    parent_dir = xml_path.parent
    stem = xml_path.stem
    match = re.match(r"(.+)_\d+$", stem)
    if not match:
        return []
    base = match.group(1)

    # Collect mulu entries from all juan files
    flat: list[TocEntry] = []
    seen: set[tuple[int, str]] = set()
    juan_files = sorted(parent_dir.glob(f"{base}_*.xml"))
    for juan_file in juan_files:
        parsed = parse_xml(juan_file)
        for m in parsed.mulu:
            level = int(m["level"])
            text = m["text"]
            key = (level, text)
            if key in seen:
                continue
            seen.add(key)
            flat.append(
                TocEntry(
                    level=level,
                    text=text,
                    type=m["type"],
                    juan=parsed.juan,
                    anchor=f"mulu-{text}",
                )
            )

    if flat:
        return _nest(flat)

    # Fallback: generate a simple juan list
    return [
        TocEntry(level=1, text=f"卷{i + 1}", type="", juan=i + 1)
        for i in range(len(juan_files))
    ]


def _nest(flat: list[TocEntry]) -> list[TocEntry]:
    """Convert flat list with levels into a nested tree."""
    root: list[TocEntry] = []
    stack: list[TocEntry] = []

    for entry in flat:
        while stack and stack[-1].level >= entry.level:
            stack.pop()
        if stack:
            stack[-1].children.append(entry)
        else:
            root.append(entry)
        stack.append(entry)

    return root
