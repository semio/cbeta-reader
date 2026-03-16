# CBETA Reader

A minimal CBETA reader for Linux (CBreader doesn't support Linux).

## Requirements

- Customizable fonts/backgrounds (dark mode, sepia, font size, font family)
- Browsable index of the full bookcase and per-book table of contents
- Nice, clean reading experience for classical Chinese Buddhist texts

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
