# CBETA Reader

A minimal CBETA reader for Linux (CBreader doesn't support Linux).

## Requirements

- Customizable fonts/backgrounds (dark mode, sepia, font size, font family)
- Browsable index of the full bookcase and per-book table of contents
- Nice, clean reading experience for classical Chinese Buddhist texts

## Code Formatting

After editing code, format with the appropriate tool:
- Python: `ruff check --fix && ruff format`
- JS/CSS: `prettier --write <files>`
- Jinja2 templates: `djlint --reformat <files>`

## Architecture

- Core Python library (no UI dependencies) for XML parsing, catalog, navigation
- Thin frontend adapters (Flask first, then optionally PyQt6 or others)

## CBETA Data

**Path:** `./data/Bookcase/CBETA` (relative to project root)

**Structure:**
- `simple_nav.xhtml` / `advance_nav.xhtml` / `bulei_nav.xhtml` — catalog navigation files
- `catalog.txt` — CSV-like: collection, category, volume, text_no, juan_count, title, author
- `XML/{collection}/{volume}/{volume}n{text_no}_{juan}.xml` — TEI XML P5 files
  - e.g., `XML/T/T01/T01n0001_001.xml` = Taishō vol.1, text 1, fascicle 1
  - 26 collections: A, B, C, CC, D, F, G, GA, GB, I, J, K, L, LC, M, N, P, S, T, TX, U, X, Y, YP, ZS, ZW
- TEI XML contains: teiHeader (metadata, char declarations), body with milestones, lb, notes, app/lem/rdg (critical apparatus), cb:mulu (table of contents entries), paragraphs
- Special characters defined in `<charDecl>` with Unicode mappings and PUA fallbacks
- `gaiji-CB/` and `font/` directories contain custom character images/fonts

## XML Parsing: Known Hurdles & Solutions

Issues encountered and resolved while building the TEI XML parser:

1. **Gaiji (外字) character resolution** — CBETA uses Private Use Area (PUA) codepoints for rare characters. The `<charDecl>` section in each file maps these to Unicode via `<mapping type="unicode">`, but some chars lack a Unicode mapping entirely. Solution: build a char map from `<charDecl>`, preferring Unicode mappings, then falling back to the `<charDecl>` composition/description text for rare chars with no Unicode equivalent.

2. **cb:mulu (目次) anchor placement** — `<cb:mulu>` elements define TOC entries but are not always followed by a `<head>` element. Initially we only emitted anchor spans when the next sibling was `<head>`, which broke ~6,900 TOC links in the T collection alone. Fix: also emit anchors when mulu is followed by `<p>`, `<lg>`, `<l>`, or other block elements. Additionally, when a mulu is followed by a `<cb:div>` containing another nested mulu (e.g. 1節→1項 in T30n1579), the outer mulu's pending anchor was overwritten and lost. Fix: emit any unconsumed pending anchor before setting a new one.

3. **Inline notes vs commentary paragraphs** — `<note place="inline">` inside `<p>` can be either a small annotation within running text or the entire content of a commentary paragraph (`<p cb:place="inline">`). Naively styling all paragraphs containing inline notes as commentary broke texts like X02n0193 where the note is just a small part of a regular paragraph. Fix: only apply the commentary/note style when the `<note>` is the first real child with no preceding text content.

4. **Redundant structural elements** — `<cb:jhead>`, `<cb:jfoot>`, and `<cb:juan>` are structural markers that duplicate information already captured elsewhere (juan number, headers). Rendering them produced duplicate headings. Fix: skip these elements entirely during body traversal.

5. **Bilingual annotations (cb:tt)** — Some texts contain `<cb:tt>` elements with parallel Chinese and Pali/Sanskrit text. Rendering both clutters the reading experience. Fix: filter to show only the Chinese text child, hiding the foreign-language parallel.

6. **Critical apparatus (app/lem/rdg)** — Textual variants are encoded as `<app><lem>…</lem><rdg>…</rdg></app>`. The reader renders only the lemma (main reading) and ignores variant readings to keep the text clean.

7. **List/item elements** — Some texts use `<list>` and `<item>` for structured content. These needed explicit handling to render as proper paragraphs with their HTML content preserved, rather than being silently dropped.

8. **Page-break anchors for reading position** — Pixel-based scroll positions broke across font size or window changes. Fix: emit `<pb>` milestone elements as named anchor spans in the HTML output, then track reading position and bookmarks by the nearest pb/mulu anchor ID instead of scroll offset.
