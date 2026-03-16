"""Flask web application for CBETA Reader."""

from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree as ET

from flask import Flask, render_template, abort

from .catalog import Catalog
from .parser import parse_xml
from .toc import build_toc

CBETA_PATH = Path(__file__).resolve().parent.parent / "data" / "Bookcase" / "CBETA"

app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent.parent / "templates"),
    static_folder=str(Path(__file__).parent.parent / "static"),
)
catalog = Catalog(CBETA_PATH)

app.jinja_env.globals["href_to_id_juan"] = lambda href: _href_to_id_juan(href)
app.jinja_env.globals["get_text_meta"] = lambda href: _get_text_meta(href)


_meta_cache: dict[str, tuple[str, str]] = {}


def _get_text_meta(href: str) -> tuple[str, str]:
    """Extract (extent, author) from the XML header."""
    stem = Path(href).stem
    base = re.sub(r"_\d+$", "", stem)
    if base in _meta_cache:
        return _meta_cache[base]
    first_juan = re.sub(r"_\d+\.xml$", "_001.xml", href)
    xml_path = CBETA_PATH / first_juan
    if not xml_path.exists():
        _meta_cache[base] = ("", "")
        return ("", "")
    extent = ""
    author = ""
    try:
        for _, elem in ET.iterparse(xml_path, events=("end",)):
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if tag == "extent" and not extent:
                extent = (elem.text or "").strip()
            elif tag == "author" and not author:
                author = (elem.text or "").strip()
            if tag == "fileDesc":
                break
    except ET.ParseError:
        pass
    _meta_cache[base] = (extent, author)
    return (extent, author)


def _href_to_xml_path(href: str) -> Path:
    """Convert an XML href like 'XML/T/T01/T01n0001_001.xml' to a filesystem path."""
    return CBETA_PATH / href


def _href_to_id_juan(href: str) -> tuple[str, int]:
    """Extract (text_id, juan) from href. E.g. 'XML/T/T01/T01n0001_003.xml' -> ('T01n0001', 3)."""
    stem = Path(href).stem  # T01n0001_003
    match = re.match(r"(.+)_(\d+)$", stem)
    if match:
        return match.group(1), int(match.group(2))
    return stem, 1


def _id_juan_to_href(text_id: str, juan: int) -> str | None:
    """Convert text_id + juan to XML href, or None if file doesn't exist."""
    # text_id like T01n0001 -> collection=T, vol_dir=T01
    match = re.match(r"([A-Z]+)(\d+)n(.+)$", text_id)
    if not match:
        return None
    collection, vol, text_no = match.groups()
    vol_dir = f"{collection}{vol}"
    fname = f"{text_id}_{juan:03d}.xml"
    xml_path = CBETA_PATH / "XML" / collection / vol_dir / fname
    if xml_path.exists():
        return str(xml_path.relative_to(CBETA_PATH))
    return None


@app.route("/")
def index():
    """Browse the catalog."""
    nav = catalog.load_nav()
    return render_template("index.html", collections=nav)


@app.route("/read/<text_id>/<int:juan>")
def read_text(text_id: str, juan: int):
    """Read a specific juan of a text."""
    href = _id_juan_to_href(text_id, juan)
    if href is None:
        abort(404)
    xml_path = _href_to_xml_path(href)

    parsed = parse_xml(xml_path)

    # Prev/next juan
    prev_juan = juan - 1 if _id_juan_to_href(text_id, juan - 1) else None
    next_juan = juan + 1 if _id_juan_to_href(text_id, juan + 1) else None

    # Build TOC for sidebar
    toc_href = _id_juan_to_href(text_id, 1) or href
    toc = build_toc(CBETA_PATH, toc_href)

    return render_template(
        "reader.html",
        text=parsed,
        text_id=text_id,
        juan=juan,
        prev_juan=prev_juan,
        next_juan=next_juan,
        toc=toc,
    )


@app.route("/toc/<text_id>")
def text_toc(text_id: str):
    """Full table of contents for a text."""
    href = _id_juan_to_href(text_id, 1)
    if href is None:
        abort(404)
    parsed = parse_xml(_href_to_xml_path(href))
    toc = build_toc(CBETA_PATH, href)
    return render_template("toc.html", text=parsed, toc=toc, text_id=text_id)


def main():
    app.run(debug=True, host="0.0.0.0", port=5000)
