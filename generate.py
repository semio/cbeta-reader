"""Generate static HTML pages from the Flask app.

Usage:
    uv run python generate.py                # all collections
    uv run python generate.py T              # just T (大正新脩大藏經)
    uv run python generate.py T X            # T and X collections
    uv run python generate.py --list         # list available collections
"""

import argparse
import glob
import re
import shutil
import time
from multiprocessing import Pool, cpu_count
from pathlib import Path

from cbeta_reader.app import CBETA_PATH, app, catalog

OUTPUT_DIR = Path("dist")
XML_DIR = CBETA_PATH / "XML"


def list_collections() -> list[str]:
    """List available collection codes from the XML directory."""
    return sorted(p.name for p in XML_DIR.iterdir() if p.is_dir())


def _xml_to_route(xml_path: str) -> str | None:
    """Convert XML path to route, e.g. '.../T01n0001_003.xml' -> '/read/T01n0001/3'."""
    stem = Path(xml_path).stem
    m = re.match(r"(.+)_(\d+)$", stem)
    if not m:
        return None
    text_id = m.group(1)
    juan = int(m.group(2))
    return f"/read/{text_id}/{juan}"


def render_route(route: str) -> str:
    """Render a single route and write to disk. Returns status message."""
    with app.test_request_context(route):
        try:
            resp = app.full_dispatch_request()
            if resp.status_code != 200:
                return f"SKIP {route} (status {resp.status_code})"
            page_dir = OUTPUT_DIR / route.lstrip("/")
            page_dir.mkdir(parents=True, exist_ok=True)
            data = resp.get_data()
            (page_dir / "index.html").write_bytes(data)
            return f"OK {route} ({len(data) // 1024} KB)"
        except Exception as e:
            return f"ERR {route}: {e}"


def _collection_codes(nav_category) -> set[str]:
    """Extract all collection codes (e.g. {'T'}, {'ZW', 'ZS', 'LC', 'TX'}) from a nav category."""
    codes: set[str] = set()
    for item in nav_category.children:
        if hasattr(item, "href"):
            parts = item.href.split("/")
            if len(parts) > 1:
                codes.add(parts[1])
        if hasattr(item, "children"):
            codes.update(_collection_codes(item))
    return codes


def _generate_index(out: Path, collections: list[str]) -> None:
    """Generate index.html filtered to only the selected collections."""
    nav = catalog.load_nav()
    coll_set = set(collections)
    filtered = [c for c in nav if _collection_codes(c) & coll_set]
    with app.test_request_context("/"):
        from flask import render_template

        html = render_template("index.html", collections=filtered)
        (out / "index.html").write_text(html)
    print(f"Generated index.html ({len(filtered)} collections)")


def _generate_404(out: Path) -> None:
    """Generate a 404.html page for missing/non-generated collections."""
    html = """\
<!DOCTYPE html>
<html lang="zh-Hant" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>頁面不存在 — CBETA Reader</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div style="max-width: var(--content-width); margin: 20vh auto; padding: 0 1rem; text-align: center;">
        <h1 style="font-size: 2rem; margin-bottom: 1rem;">此頁面不存在</h1>
        <p style="color: var(--fg-secondary); margin-bottom: 2rem;">該經典尚未收錄或尚未上傳。</p>
        <a href="/" style="color: var(--accent);">返回首頁</a>
    </div>
    <script src="/static/base.js"></script>
</body>
</html>
"""
    (out / "404.html").write_text(html)
    print("Generated 404.html")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate static CBETA Reader pages")
    parser.add_argument(
        "collections",
        nargs="*",
        help="Collection codes to generate (e.g. T X). Omit for all.",
    )
    parser.add_argument(
        "--list", action="store_true", help="List available collections and exit"
    )
    parser.add_argument(
        "-o", "--output", default="dist", help="Output directory (default: dist)"
    )
    args = parser.parse_args()

    available = list_collections()

    if args.list:
        print(f"Available collections ({len(available)}):")
        for c in available:
            count = len(glob.glob(str(XML_DIR / c / "**/*.xml"), recursive=True))
            print(f"  {c:4s}  {count:>5d} pages")
        return

    global OUTPUT_DIR
    OUTPUT_DIR = Path(args.output)

    collections = args.collections or available
    unknown = [c for c in collections if c not in available]
    if unknown:
        print(f"Unknown collections: {', '.join(unknown)}")
        print(f"Available: {', '.join(available)}")
        return

    out = OUTPUT_DIR
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    # Copy static files
    static_src = Path(__file__).parent / "static"
    shutil.copytree(static_src, out / "static")

    # Generate index page (filtered to selected collections)
    _generate_index(out, collections)

    # Generate 404 page for missing/non-generated collections
    _generate_404(out)

    # Collect routes for selected collections
    routes = []
    for coll in collections:
        xml_files = sorted(
            glob.glob(str(XML_DIR / coll / "**/*.xml"), recursive=True)
        )
        for f in xml_files:
            route = _xml_to_route(f)
            if route:
                routes.append(route)
        print(f"  {coll}: {len(xml_files)} pages")

    print(f"Generating {len(routes)} reader pages with {cpu_count()} workers...")

    t0 = time.time()
    workers = min(cpu_count(), len(routes))
    done = 0
    errors = 0
    with Pool(workers) as pool:
        for result in pool.imap_unordered(render_route, routes, chunksize=32):
            done += 1
            if result.startswith("ERR") or result.startswith("SKIP"):
                errors += 1
                print(result)
            if done % 500 == 0:
                elapsed = time.time() - t0
                rate = done / elapsed
                eta = (len(routes) - done) / rate
                print(f"  {done}/{len(routes)} ({rate:.0f}/s, ETA {eta:.0f}s)")

    elapsed = time.time() - t0
    total_html = sum(1 for _ in out.rglob("*.html"))
    total_size = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    print(f"\nDone in {elapsed:.1f}s")
    print(f"Total files: {total_html} HTML + static")
    print(f"Total size: {total_size / 1024 / 1024:.0f} MB")
    if errors:
        print(f"Errors/skipped: {errors}")


if __name__ == "__main__":
    main()
