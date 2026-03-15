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
        # Fallback to normalized form
        if char_id not in char_map:
            for prop in char.findall(f"{{{TEI_NS}}}charProp"):
                name_el = prop.find(f"{{{TEI_NS}}}localName")
                val_el = prop.find(f"{{{TEI_NS}}}value")
                if (
                    name_el is not None
                    and name_el.text == "normalized form"
                    and val_el is not None
                    and val_el.text
                ):
                    char_map[char_id] = val_el.text
                    break
    return char_map


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
            # Skip footnotes in running text
            pass
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
    _walk_body(body, char_map, parts)
    return "".join(parts)


def _walk_body(el: etree._Element, char_map: dict[str, str], parts: list[str]) -> None:
    tag = etree.QName(el.tag).localname if isinstance(el.tag, str) else ""

    if tag == "lb":
        # Line break — just add a newline within paragraphs
        return
    elif tag == "pb":
        # Page break
        return
    elif tag == "milestone":
        n = el.get("n", "")
        if el.get("unit") == "juan" and n:
            parts.append(f'<h2 class="juan">第{_to_chinese_num(n)}卷</h2>\n')
        return
    elif tag == "head":
        parts.append("<h3>")
        parts.append(_escape(_text_content(el, char_map)))
        parts.append("</h3>\n")
        return
    elif tag == "p":
        parts.append('<p class="body-text">')
        parts.append(_escape(_text_content(el, char_map)))
        parts.append("</p>\n")
        return
    elif tag in ("byline",):
        parts.append('<p class="byline">')
        parts.append(_escape(_text_content(el, char_map)))
        parts.append("</p>\n")
        return
    elif tag == "lg":
        parts.append('<div class="verse">')
        for child in el:
            _walk_body(child, char_map, parts)
        parts.append("</div>\n")
        if el.tail and el.tail.strip():
            parts.append(_escape(el.tail))
        return
    elif tag == "l":
        parts.append('<p class="verse-line">')
        parts.append(_escape(_text_content(el, char_map)))
        parts.append("</p>\n")
        return
    elif tag in ("note",):
        return  # Skip notes
    elif tag in ("app",):
        lem = el.find(f"{{{TEI_NS}}}lem")
        if lem is not None:
            _walk_body(lem, char_map, parts)
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
    elif tag == "docNumber":
        return  # Skip "No. X" markers
    elif tag in ("div", "mulu"):
        # cb:div — walk children
        for child in el:
            _walk_body(child, char_map, parts)
        return

    # Default: recurse into children
    if el.text and el.text.strip():
        parts.append(_escape(el.text))
    for child in el:
        _walk_body(child, char_map, parts)
    if el.tail and el.tail.strip():
        parts.append(_escape(el.tail))


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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
