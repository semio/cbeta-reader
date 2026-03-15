"""Flask web application for CBETA Reader."""

from __future__ import annotations

import re
from pathlib import Path

from flask import Flask, render_template, abort

from .catalog import Catalog
from .parser import parse_xml

CBETA_PATH = Path("/home/semio/Downloads/bookcase_v098_20251216/Bookcase/CBETA")

app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent.parent / "templates"),
    static_folder=str(Path(__file__).parent.parent / "static"),
)
catalog = Catalog(CBETA_PATH)


@app.route("/")
def index():
    """Browse the catalog."""
    nav = catalog.load_nav()
    return render_template("index.html", collections=nav)


@app.route("/text/<path:href>")
def read_text(href: str):
    """Read a specific XML file."""
    xml_path = CBETA_PATH / href
    if not xml_path.exists():
        abort(404)

    parsed = parse_xml(xml_path)

    # Figure out prev/next juan navigation
    parent_dir = xml_path.parent
    stem = xml_path.stem  # e.g. T01n0001_001
    match = re.match(r"(.+)_(\d+)$", stem)
    prev_href = next_href = None
    if match:
        base, juan_str = match.groups()
        juan_num = int(juan_str)
        # Previous
        if juan_num > 1:
            prev_file = parent_dir / f"{base}_{juan_num - 1:03d}.xml"
            if prev_file.exists():
                prev_href = str(prev_file.relative_to(CBETA_PATH))
        # Next
        next_file = parent_dir / f"{base}_{juan_num + 1:03d}.xml"
        if next_file.exists():
            next_href = str(next_file.relative_to(CBETA_PATH))

    return render_template(
        "reader.html",
        text=parsed,
        href=href,
        prev_href=prev_href,
        next_href=next_href,
    )


def main():
    app.run(debug=True, port=5000)
