"""Parse CBETA TEI XML into readable HTML."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

TEI_NS = "http://www.tei-c.org/ns/1.0"
CB_NS = "http://www.cbeta.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"

NSMAP = {"tei": TEI_NS, "cb": CB_NS}


@dataclass
class ParsedText:
    title: str = ""
    author: str = ""
    juan: int = 1
    body_html: str = ""
    doc_number: str = ""
    mulu: list[dict[str, str]] = field(default_factory=list)


def _get_char_map(header: etree._Element) -> dict[str, str]:
    """Build a map from char ID -> unicode character from charDecl."""
    char_map: dict[str, str] = {}
    for char in header.iter(f"{{{TEI_NS}}}char"):
        char_id = char.get(f"{{{XML_NS}}}id", "")
        # Prefer unicode mapping
        for mapping in char.findall(f"{{{TEI_NS}}}mapping"):
            mtype = mapping.get("type", "")
            if mtype == "unicode" and mapping.text:
                code = mapping.text.strip()
                if code.startswith("U+"):
                    try:
                        char_map[char_id] = chr(int(code[2:], 16))
                    except ValueError:
                        pass
                break
        # Fallback to normalized form, then composition
        if char_id not in char_map:
            normalized = ""
            composition = ""
            for prop in char.findall(f"{{{TEI_NS}}}charProp"):
                name_el = prop.find(f"{{{TEI_NS}}}localName")
                val_el = prop.find(f"{{{TEI_NS}}}value")
                if name_el is None or val_el is None or not val_el.text:
                    continue
                if name_el.text == "normalized form":
                    normalized = val_el.text
                elif name_el.text == "composition":
                    composition = val_el.text
            if normalized:
                char_map[char_id] = normalized
            elif composition:
                char_map[char_id] = composition
    return char_map


def _content_html(el: etree._Element, char_map: dict[str, str]) -> str:
    """Like _text_content but returns HTML, wrapping inline notes in spans."""
    parts: list[str] = []
    if el.text:
        parts.append(_escape(el.text))
    for child in el:
        tag = etree.QName(child.tag).localname if isinstance(child.tag, str) else ""
        if tag == "g":
            ref = child.get("ref", "").lstrip("#")
            parts.append(_escape(char_map.get(ref, child.text or "?")))
        elif tag == "note":
            if child.get("place") == "inline":
                note_text = _text_content(child, char_map)
                parts.append(f'<span class="inline-note">（{_escape(note_text)}）</span>')
        elif tag == "app":
            lem = child.find(f"{{{TEI_NS}}}lem")
            if lem is not None:
                parts.append(_content_html(lem, char_map))
        elif tag == "rdg":
            pass
        elif tag == "tt":
            for t in child:
                t_tag = etree.QName(t.tag).localname if isinstance(t.tag, str) else ""
                if t_tag == "t":
                    lang = t.get(f"{{{XML_NS}}}lang", "")
                    if lang.startswith("zh"):
                        parts.append(_escape(_text_content(t, char_map)))
                        if t.tail:
                            parts.append(_escape(t.tail))
                        break
        elif tag in ("lb", "pb", "milestone"):
            pass
        elif tag == "space":
            qty = child.get("quantity", "1")
            try:
                parts.append("\u3000" * int(qty))
            except ValueError:
                parts.append("\u3000")
        else:
            parts.append(_content_html(child, char_map))
        if child.tail:
            parts.append(_escape(child.tail))
    return "".join(parts)


def _text_content(el: etree._Element, char_map: dict[str, str]) -> str:
    """Recursively extract text from an element, resolving gaiji references."""
    parts: list[str] = []
    if el.text:
        parts.append(el.text)
    for child in el:
        tag = etree.QName(child.tag).localname if isinstance(child.tag, str) else ""
        if tag == "g":
            # Gaiji reference like <g ref="#CB00166"/>
            ref = child.get("ref", "").lstrip("#")
            parts.append(char_map.get(ref, child.text or "?"))
        elif tag == "note":
            if child.get("place") == "inline":
                parts.append(_text_content(child, char_map))
            # Skip non-inline notes
        elif tag == "app":
            # Use lem (main reading) from critical apparatus
            lem = child.find(f"{{{TEI_NS}}}lem")
            if lem is not None:
                parts.append(_text_content(lem, char_map))
        elif tag == "rdg":
            pass  # Skip variant readings
        elif tag == "tt":
            # cb:tt — bilingual annotation; keep only Chinese text
            for t in child:
                t_tag = etree.QName(t.tag).localname if isinstance(t.tag, str) else ""
                if t_tag == "t":
                    lang = t.get(f"{{{XML_NS}}}lang", "")
                    if lang.startswith("zh"):
                        parts.append(_text_content(t, char_map))
                        if t.tail:
                            parts.append(t.tail)
                        break
        elif tag in ("lb", "pb", "milestone"):
            pass  # Skip structural markers
        elif tag == "space":
            qty = child.get("quantity", "1")
            try:
                parts.append("\u3000" * int(qty))
            except ValueError:
                parts.append("\u3000")
        else:
            parts.append(_text_content(child, char_map))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def parse_xml(path: Path) -> ParsedText:
    """Parse a CBETA TEI XML file into structured content."""
    tree = etree.parse(str(path))
    root = tree.getroot()
    result = ParsedText()

    # Extract metadata from header
    header = root.find(f"{{{TEI_NS}}}teiHeader")
    if header is not None:
        title_el = header.find(f".//{{{TEI_NS}}}title[@level='m']")
        if title_el is not None:
            result.title = title_el.text or ""
        author_el = header.find(f".//{{{TEI_NS}}}author")
        if author_el is not None:
            result.author = _text_content(author_el, {})

    char_map = _get_char_map(header) if header is not None else {}

    # Extract body
    body = root.find(f".//{{{TEI_NS}}}body")
    if body is None:
        return result

    # Get juan number from milestone
    for ms in body.iter(f"{{{TEI_NS}}}milestone"):
        if ms.get("unit") == "juan":
            try:
                result.juan = int(ms.get("n", "1"))
            except ValueError:
                pass
            break

    # Extract doc number (e.g. "No. 278 [No. 279]")
    doc_num_el = body.find(f".//{{{CB_NS}}}docNumber")
    if doc_num_el is not None and doc_num_el.text:
        result.doc_number = doc_num_el.text.strip()

    # Extract mulu (table of contents entries)
    for mulu in body.iter(f"{{{CB_NS}}}mulu"):
        level = mulu.get("level", "1")
        mulu_type = mulu.get("type", "")
        text = mulu.text or ""
        if text:
            result.mulu.append({"level": level, "type": mulu_type, "text": text})

    # Convert body to HTML
    result.body_html = _body_to_html(body, char_map)
    return result


def _body_to_html(body: etree._Element, char_map: dict[str, str]) -> str:
    """Convert TEI body to clean HTML."""
    parts: list[str] = []
    state: dict[str, str | None] = {"pending_mulu": None}
    _walk_body(body, char_map, parts, state)
    return "".join(parts)


def _emit_pb_anchors(el: etree._Element, parts: list[str]) -> None:
    """Emit pb anchor spans found as direct children of el."""
    for child in el:
        tag = etree.QName(child.tag).localname if isinstance(child.tag, str) else ""
        if tag == "pb":
            xml_id = child.get(f"{{{XML_NS}}}id", "")
            if xml_id:
                parts.append(f'<span class="pb" id="{_escape_attr(xml_id)}"></span>')


def _walk_body(
    el: etree._Element,
    char_map: dict[str, str],
    parts: list[str],
    state: dict[str, str | None],
) -> None:
    tag = etree.QName(el.tag).localname if isinstance(el.tag, str) else ""

    # Emit pending mulu anchor before any block-level element (when not consumed by <head>)
    if tag in ("p", "lg", "l", "byline", "item", "list") and state.get("pending_mulu"):
        anchor_id = _escape_attr(str(state["pending_mulu"]))
        parts.append(f'<span class="mulu-anchor" id="mulu-{anchor_id}"></span>')
        state["pending_mulu"] = None

    if tag == "lb":
        return
    elif tag == "pb":
        xml_id = el.get(f"{{{XML_NS}}}id", "")
        if xml_id:
            parts.append(f'<span class="pb" id="{_escape_attr(xml_id)}"></span>')
        return
    elif tag == "mulu":
        # Track mulu text so the next <head> gets an anchor
        text = el.text or ""
        if text:
            state["pending_mulu"] = text
        for child in el:
            _walk_body(child, char_map, parts, state)
        return
    elif tag == "milestone":
        n = el.get("n", "")
        if el.get("unit") == "juan" and n:
            parts.append(f'<h2 class="juan">第{_to_chinese_num(n)}卷</h2>\n')
        return
    elif tag == "head":
        _emit_pb_anchors(el, parts)
        anchor = state.get("pending_mulu")
        if anchor:
            anchor_id = _escape_attr(anchor)
            parts.append(f'<h3 id="mulu-{anchor_id}">')
            state["pending_mulu"] = None
        else:
            parts.append("<h3>")
        parts.append(_content_html(el, char_map))
        parts.append("</h3>\n")
        return
    elif tag == "p":
        _emit_pb_anchors(el, parts)
        cb_place = el.get(f"{{{CB_NS}}}place", "")
        # Commentary: cb:place="inline", note is first real child, no text before it
        first_real = next(
            (
                c
                for c in el
                if (etree.QName(c.tag).localname if isinstance(c.tag, str) else "")
                not in ("lb", "pb")
            ),
            None,
        )
        is_commentary = (
            cb_place == "inline"
            and first_real is not None
            and (etree.QName(first_real.tag).localname if isinstance(first_real.tag, str) else "")
            == "note"
            and first_real.get("place") == "inline"
            and not (el.text or "").strip()
        )
        if is_commentary:
            parts.append('<p class="inline-note">')
        else:
            parts.append('<p class="body-text">')
        parts.append(_content_html(el, char_map))
        parts.append("</p>\n")
        return
    elif tag in ("byline",):
        _emit_pb_anchors(el, parts)
        parts.append('<p class="byline">')
        parts.append(_escape(_text_content(el, char_map)))
        parts.append("</p>\n")
        return
    elif tag == "lg":
        parts.append('<div class="verse">')
        for child in el:
            _walk_body(child, char_map, parts, state)
        parts.append("</div>\n")
        if el.tail and el.tail.strip():
            parts.append(_escape(el.tail))
        return
    elif tag == "l":
        _emit_pb_anchors(el, parts)
        parts.append('<p class="verse-line">')
        parts.append(_content_html(el, char_map))
        parts.append("</p>\n")
        return
    elif tag == "note":
        if el.get("place") == "inline":
            _emit_pb_anchors(el, parts)
            note_text = _escape(_text_content(el, char_map))
            parts.append(f'<span class="inline-note">（{note_text}）</span>')
        return  # Skip non-inline notes
    elif tag in ("app",):
        lem = el.find(f"{{{TEI_NS}}}lem")
        if lem is not None:
            _walk_body(lem, char_map, parts, state)
        return
    elif tag in ("rdg",):
        return
    elif tag == "tt":
        # cb:tt — bilingual annotation; keep only Chinese text
        for child in el:
            child_tag = etree.QName(child.tag).localname if isinstance(child.tag, str) else ""
            if child_tag == "t":
                lang = child.get(f"{{{XML_NS}}}lang", "")
                if lang.startswith("zh"):
                    parts.append(_escape(_text_content(child, char_map)))
                    break
        if el.tail and el.tail.strip():
            parts.append(_escape(el.tail))
        return
    elif tag == "t":
        # cb:t outside of cb:tt — only render Chinese
        lang = el.get(f"{{{XML_NS}}}lang", "")
        if not lang.startswith("zh") and lang:
            return
        parts.append(_escape(_text_content(el, char_map)))
        if el.tail and el.tail.strip():
            parts.append(_escape(el.tail))
        return
    elif tag in ("docNumber", "jhead", "jfoot", "juan"):
        return  # Skip redundant structural markers
    elif tag in ("div", "list"):
        for child in el:
            _walk_body(child, char_map, parts, state)
        return
    elif tag == "item":
        _emit_pb_anchors(el, parts)
        parts.append('<p class="body-text">')
        parts.append(_content_html(el, char_map))
        parts.append("</p>\n")
        return

    # Default: recurse into children
    if el.text and el.text.strip():
        parts.append(_escape(el.text))
    for child in el:
        _walk_body(child, char_map, parts, state)
    if el.tail and el.tail.strip():
        parts.append(_escape(el.tail))


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _escape_attr(text: str) -> str:
    """Escape text for use as an HTML attribute value."""
    return (
        text.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
    )


def _to_chinese_num(n: str) -> str:
    """Convert a number string to Chinese numerals (simple version)."""
    digits = "〇一二三四五六七八九"
    try:
        num = int(n)
    except ValueError:
        return n
    if num <= 0:
        return n
    if num <= 10:
        return ["", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"][num]
    if num < 20:
        return "十" + (digits[num - 10] if num > 10 else "")
    if num < 100:
        tens = num // 10
        ones = num % 10
        return digits[tens] + "十" + (digits[ones] if ones else "")
    # For larger numbers just use digits
    return "".join(digits[int(d)] for d in str(num))
