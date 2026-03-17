"""Tests for the CBETA TEI XML parser."""

from cbeta_reader.parser import (
    _body_to_html,
    _get_char_map,
    parse_xml,
)
from lxml import etree

TEI_NS = "http://www.tei-c.org/ns/1.0"
CB_NS = "http://www.cbeta.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"


def _make_body(inner_xml: str) -> etree._Element:
    """Build a TEI <body> element from inner XML string."""
    xml = f"""<body xmlns="{TEI_NS}" xmlns:cb="{CB_NS}"
              xmlns:xml="{XML_NS}">{inner_xml}</body>"""
    return etree.fromstring(xml)


def _render(inner_xml: str, char_map: dict | None = None) -> str:
    """Render inner body XML to HTML."""
    body = _make_body(inner_xml)
    return _body_to_html(body, char_map or {})


def _make_header(inner_xml: str) -> etree._Element:
    """Build a TEI <teiHeader> element."""
    xml = f"""<teiHeader xmlns="{TEI_NS}" xmlns:cb="{CB_NS}"
              xmlns:xml="{XML_NS}">{inner_xml}</teiHeader>"""
    return etree.fromstring(xml)


# --- char map / gaiji ---


class TestCharMap:
    def test_unicode_mapping(self):
        header = _make_header("""
        <encodingDesc><charDecl>
            <char xml:id="CB00501">
                <mapping type="unicode">U+4B6E</mapping>
            </char>
        </charDecl></encodingDesc>
        """)
        cm = _get_char_map(header)
        assert cm["CB00501"] == "\u4B6E"

    def test_normalized_form_fallback(self):
        header = _make_header("""
        <encodingDesc><charDecl>
            <char xml:id="CB00100">
                <charProp>
                    <localName>normalized form</localName>
                    <value>塔</value>
                </charProp>
            </char>
        </charDecl></encodingDesc>
        """)
        cm = _get_char_map(header)
        assert cm["CB00100"] == "塔"

    def test_composition_fallback(self):
        """Chars with only a composition (like CB02253) should use it as fallback."""
        header = _make_header("""
        <encodingDesc><charDecl>
            <char xml:id="CB02253">
                <charProp>
                    <localName>composition</localName>
                    <value>[口*(黍-禾+利)]</value>
                </charProp>
                <mapping cb:dec="985293" type="PUA">U+F08CD</mapping>
            </char>
        </charDecl></encodingDesc>
        """)
        cm = _get_char_map(header)
        assert cm["CB02253"] == "[口*(黍-禾+利)]"

    def test_unicode_preferred_over_composition(self):
        header = _make_header("""
        <encodingDesc><charDecl>
            <char xml:id="CB00501">
                <mapping type="unicode">U+4B6E</mapping>
                <charProp>
                    <localName>composition</localName>
                    <value>[some+comp]</value>
                </charProp>
            </char>
        </charDecl></encodingDesc>
        """)
        cm = _get_char_map(header)
        assert cm["CB00501"] == "\u4B6E"

    def test_missing_char_renders_question_mark(self):
        body = _make_body('<p xml:id="p1">text<g ref="#MISSING"/>more</p>')
        html = _body_to_html(body, {})
        assert "?" in html


# --- jhead / jfoot / juan skipping ---


class TestSkipRedundantElements:
    def test_jhead_skipped(self):
        """cb:jhead content should not appear in output (T48n2014 stray 證 fix)."""
        html = _render("""
        <milestone unit="juan" n="1"/>
        <cb:juan n="001" fun="open">
            <cb:jhead>永嘉證道歌</cb:jhead>
        </cb:juan>
        <byline type="author">唐慎水沙門玄覺撰</byline>
        """)
        assert "永嘉證道歌" not in html
        assert "唐慎水沙門玄覺撰" in html

    def test_jfoot_skipped(self):
        html = _render('<cb:jfoot>永嘉證道歌終</cb:jfoot>')
        assert "永嘉證道歌終" not in html

    def test_juan_element_skipped(self):
        html = _render("""
        <cb:juan n="001" fun="open">
            <cb:jhead>卷第一</cb:jhead>
        </cb:juan>
        """)
        assert "卷第一" not in html

    def test_milestone_renders_juan_heading(self):
        html = _render('<milestone unit="juan" n="1"/>')
        assert '<h2 class="juan">第一卷</h2>' in html


# --- inline notes ---


class TestInlineNotes:
    def test_inline_note_in_paragraph_with_parens(self):
        """Inline notes within <p> should render with parentheses (T12n0369 fix)."""
        html = _render("""
        <p xml:id="p1">那<note place="inline">上</note>謨菩<note place="inline">上</note>陀夜</p>
        """)
        assert '那<span class="inline-note">（上）</span>謨菩' in html
        assert '<p class="body-text">' in html

    def test_inline_note_longer_text(self):
        html = _render("""
        <p xml:id="p1">陀夜<note place="inline">藥可反，下同</note>那謨</p>
        """)
        assert "（藥可反，下同）" in html

    def test_commentary_paragraph_styled_as_inline_note(self):
        """<p cb:place="inline"> wrapping <note place="inline"> = commentary (D13n8838)."""
        html = _render("""
        <p xml:id="p1" cb:place="inline" style="margin-left:1em">
            <note place="inline">釋曰金剛寶也</note>。
        </p>
        """)
        assert '<p class="inline-note">' in html

    def test_plain_inline_paragraph_not_styled_as_note(self):
        """<p cb:place="inline"> without note child = normal text (D13n8838 般若 fix)."""
        html = _render('<p xml:id="p1" cb:place="inline">般若。</p>')
        assert '<p class="body-text">' in html
        assert "般若" in html

    def test_dharani_paragraph_not_styled_as_note(self):
        """<p> with inline note children but no cb:place should be body-text (T12n0369)."""
        html = _render("""
        <p xml:id="p1" cb:type="dharani">那<note place="inline">上</note>謨</p>
        """)
        assert '<p class="body-text">' in html

    def test_inline_note_in_head_with_parens(self):
        """Inline notes in headings should have parentheses (T30n1564 verse count)."""
        html = _render("""
        <cb:mulu level="1" type="品">觀因緣品</cb:mulu>
        <head>觀因緣品第一<app n="001"><lem wit="【大】">
            <note place="inline">十六偈</note>
        </lem></app></head>
        """)
        assert "觀因緣品第一" in html
        assert '<span class="inline-note">（十六偈）</span>' in html

    def test_inline_note_via_walk_body_has_parens(self):
        """Inline notes rendered by _walk_body directly should also have parens (X74n1480)."""
        html = _render("""
        <list rend="no-marker">
            <item xml:id="i1">一心頂禮十方常住三寶<note place="inline">一禮畢</note></item>
        </list>
        """)
        assert "（一禮畢）" in html

    def test_inline_place_with_text_before_note_is_body_text(self):
        """<p cb:place="inline"> with text before the note = normal text (X02n0193 fix)."""
        html = _render("""
        <p xml:id="p1" cb:place="inline">佛言：「若四輩弟子<note place="inline">某甲</note>」</p>
        """)
        assert '<p class="body-text">' in html
        assert "（某甲）" in html

    def test_non_inline_notes_skipped(self):
        """Footnotes (non-inline notes) should not appear in output."""
        html = _render("""
        <p xml:id="p1">大本<note resp="Taisho" place="foot text" type="orig">大本經＝大本緣經</note>經第一</p>
        """)
        assert "大本經第一" in html
        assert "大本緣經" not in html


# --- list / item ---


class TestListItem:
    def test_item_rendered_as_paragraph(self):
        html = _render("""
        <list><item xml:id="i1">一心頂禮十方常住三寶</item></list>
        """)
        assert '<p class="body-text">一心頂禮十方常住三寶</p>' in html

    def test_item_with_inline_note(self):
        html = _render("""
        <list><item xml:id="i1">歸命禮三寶<note place="inline">一拜</note>。</item></list>
        """)
        assert "歸命禮三寶" in html
        assert "（一拜）" in html


# --- basic element rendering ---


class TestBasicRendering:
    def test_paragraph(self):
        html = _render('<p xml:id="p1">佛告須菩提。</p>')
        assert '<p class="body-text">佛告須菩提。</p>' in html

    def test_byline(self):
        html = _render('<byline type="author">唐慎水沙門玄覺撰</byline>')
        assert '<p class="byline">唐慎水沙門玄覺撰</p>' in html

    def test_verse(self):
        html = _render("""
        <lg><l>君不見。絕學無為閒道人。</l><l>不除妄想不求真。</l></lg>
        """)
        assert '<div class="verse">' in html
        assert '<p class="verse-line">君不見。絕學無為閒道人。</p>' in html

    def test_head_with_mulu_anchor(self):
        html = _render("""
        <cb:mulu level="1" type="品">觀因緣品</cb:mulu>
        <head>觀因緣品第一</head>
        """)
        assert '<h3 id="mulu-觀因緣品">觀因緣品第一</h3>' in html

    def test_head_without_mulu(self):
        html = _render("<head>長阿含經序</head>")
        assert "<h3>長阿含經序</h3>" in html

    def test_gaiji_resolved(self):
        html = _render(
            '<p xml:id="p1">text<g ref="#CB00501"/>more</p>',
            char_map={"CB00501": "䭾"},
        )
        assert "text䭾more" in html

    def test_critical_apparatus_uses_lem(self):
        html = _render("""
        <p xml:id="p1">before<app n="001">
            <lem wit="【大】">正文</lem>
            <rdg wit="【宋】">異文</rdg>
        </app>after</p>
        """)
        assert "正文" in html
        assert "異文" not in html

    def test_docnumber_skipped(self):
        html = _render('<cb:docNumber>No. 278</cb:docNumber>')
        assert "No. 278" not in html

    def test_space_element(self):
        html = _render('<p xml:id="p1">before<space quantity="2"/>after</p>')
        assert "before\u3000\u3000after" in html


# --- integration tests with real XML files ---


class TestIntegration:
    """Tests against actual CBETA XML files (skipped if data not available)."""

    DATA = "data/Bookcase/CBETA/XML"

    def _parse(self, rel_path: str):
        from pathlib import Path

        p = Path(self.DATA) / rel_path
        if not p.exists():
            import pytest

            pytest.skip(f"Data file not available: {p}")
        return parse_xml(p)

    def test_t48n2014_no_stray_text(self):
        """T48n2014: jhead content should not leak into output."""
        result = self._parse("T/T48/T48n2014_001.xml")
        # Body should start with juan heading then byline, no stray 證
        assert result.body_html.startswith('<h2 class="juan">第一卷</h2>\n<p class="byline">')

    def test_t30n1564_heading_verse_count(self):
        """T30n1564: headings should show verse count in parentheses."""
        result = self._parse("T/T30/T30n1564_001.xml")
        assert '<span class="inline-note">（十六偈）</span>' in result.body_html

    def test_t12n0369_pronunciation_notes(self):
        """T12n0369: pronunciation annotations should be in spans, not coloring whole paragraph."""
        result = self._parse("T/T12/T12n0369_001.xml")
        # 那 should be in body-text, not inline-note
        idx = result.body_html.find("那")
        start = result.body_html.rfind("<p", 0, idx)
        assert result.body_html[start:].startswith('<p class="body-text">')
        # But the annotation should be in a span
        assert '<span class="inline-note">（上）</span>' in result.body_html

    def test_t12n0369_composition_char(self):
        """T12n0369: rare char CB02253 should render as composition, not '?'."""
        result = self._parse("T/T12/T12n0369_001.xml")
        assert "?" not in result.body_html
        assert "[口*(黍-禾+利)]" in result.body_html

    def test_d13n8838_commentary_styled(self):
        """D13n8838: commentary paragraphs should be inline-note class."""
        result = self._parse("D/D13/D13n8838_001.xml")
        assert '<p class="inline-note">' in result.body_html

    def test_d13n8838_normal_text_not_styled(self):
        """D13n8838: 般若。should be body-text, not inline-note."""
        result = self._parse("D/D13/D13n8838_001.xml")
        import re

        m = re.search(r'<p class="([^"]+)">[^<]*般若。</p>', result.body_html)
        assert m is not None
        assert m.group(1) == "body-text"
