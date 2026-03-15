"""Parse CBETA catalog and navigation files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET


@dataclass
class TextEntry:
    collection: str
    category: str
    volume: str
    text_no: str
    juan_count: int
    title: str
    author: str

    @property
    def text_id(self) -> str:
        return f"{self.collection}{self.text_no}"


@dataclass
class NavCategory:
    label: str
    children: list[NavCategory | NavLink] = field(default_factory=list)


@dataclass
class NavLink:
    label: str
    href: str  # e.g. "XML/T/T01/T01n0001_001.xml"

    @property
    def text_id(self) -> str:
        """Extract text ID like 'T0001' from href."""
        fname = Path(self.href).stem  # T01n0001_001
        parts = fname.split("n")
        if len(parts) == 2:
            no = parts[1].split("_")[0]
            return f"{parts[0][0]}{no}"
        return fname


class Catalog:
    def __init__(self, cbeta_path: str | Path) -> None:
        self.base = Path(cbeta_path)
        self._entries: dict[str, TextEntry] = {}
        self._nav: list[NavCategory] = []
        self._load_catalog()

    def _load_catalog(self) -> None:
        cat_file = self.base / "catalog.txt"
        for line in cat_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(" , ")]
            if len(parts) < 7:
                continue
            entry = TextEntry(
                collection=parts[0],
                category=parts[1],
                volume=parts[2],
                text_no=parts[3],
                juan_count=int(parts[4]) if parts[4].isdigit() else 0,
                title=parts[5],
                author=parts[6] if len(parts) > 6 else "",
            )
            self._entries[entry.text_id] = entry

    def get_entry(self, text_id: str) -> TextEntry | None:
        return self._entries.get(text_id)

    def load_nav(self) -> list[NavCategory]:
        """Parse simple_nav.xhtml into a tree structure."""
        if self._nav:
            return self._nav
        nav_file = self.base / "simple_nav.xhtml"
        tree = ET.parse(nav_file)
        root = tree.getroot()
        nav = root.find(".//nav")
        if nav is None:
            return []
        self._nav = self._parse_nav_children(nav)
        return self._nav

    def _parse_nav_children(self, el: ET.Element) -> list[NavCategory]:
        """Parse top-level nav element.

        Structure: first collection has <span>Name</span><ol>...</ol> at top level.
        Subsequent collections appear as <ol><li><span>Name</span><ol>...</ol></li></ol>.
        """
        results: list[NavCategory] = []
        span = None
        for child in el:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "span":
                span = child.text or ""
            elif tag == "ol":
                if span is not None:
                    # First collection: span + ol at top level
                    cat = NavCategory(label=span)
                    cat.children = self._parse_ol(child)
                    results.append(cat)
                    span = None
                else:
                    # Subsequent collections: ol wrapping <li><span>...</span><ol>...</ol></li>
                    for item in self._parse_ol(child):
                        results.append(item)
            elif tag == "li":
                # Direct <li> children (shouldn't happen but be safe)
                for item in self._parse_ol_li(child):
                    results.append(item)
        return results

    def _parse_ol(self, ol: ET.Element) -> list[NavCategory | NavLink]:
        items: list[NavCategory | NavLink] = []
        for li in ol:
            tag = li.tag.split("}")[-1] if "}" in li.tag else li.tag
            if tag != "li":
                continue
            items.extend(self._parse_ol_li(li))
        return items

    def _parse_ol_li(self, li: ET.Element) -> list[NavCategory | NavLink]:
        span_el = li.find("span")
        link_el = li.find("cblink")
        sub_ol = li.find("ol")
        if span_el is not None:
            cat = NavCategory(label=span_el.text or "")
            if sub_ol is not None:
                cat.children = self._parse_ol(sub_ol)
            return [cat]
        elif link_el is not None:
            href = link_el.get("href", "")
            label = link_el.text or ""
            return [NavLink(label=label, href=href)]
        return []

    def xml_path(self, collection: str, volume: str, text_no: str, juan: int) -> Path:
        """Build path to a specific XML file."""
        vol_dir = f"{collection}{volume.zfill(2)}"
        fname = f"{vol_dir}n{text_no}_{juan:03d}.xml"
        return self.base / "XML" / collection / vol_dir / fname

    def list_juan_files(self, collection: str, volume: str, text_no: str) -> list[Path]:
        """List all juan files for a text."""
        vol_dir = f"{collection}{volume.zfill(2)}"
        pattern = f"{vol_dir}n{text_no}_*.xml"
        xml_dir = self.base / "XML" / collection / vol_dir
        if not xml_dir.exists():
            return []
        return sorted(xml_dir.glob(pattern))
