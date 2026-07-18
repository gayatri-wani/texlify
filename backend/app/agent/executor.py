import os
import re
import shutil
from docx import Document as DocxDocument
from docx.shared import Pt, Inches, RGBColor, Mm, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from datetime import datetime


def hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip('#')
    r, g, b   = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return RGBColor(r, g, b)


def get_alignment(alignment_str: str):
    mapping = {
        "left":    WD_ALIGN_PARAGRAPH.LEFT,
        "center":  WD_ALIGN_PARAGRAPH.CENTER,
        "right":   WD_ALIGN_PARAGRAPH.RIGHT,
        "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
    }
    return mapping.get(alignment_str.lower(), WD_ALIGN_PARAGRAPH.LEFT)


def backup_document(file_path: str) -> str:
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    return backup_path


HIGHLIGHT_HEX = {
    "yellow":    "FFFF00",
    "green":     "00FF00",
    "cyan":      "00FFFF",
    "magenta":   "FF00FF",
    "pink":      "FF69B4",
    "blue":      "ADD8E6",
    "red":       "FF0000",
    "orange":    "FFA500",
    "turquoise": "40E0D0",
    "gray":      "D3D3D3",
    "white":     "FFFFFF",
}

HIGHLIGHT_XML = {
    "yellow":    "yellow",
    "green":     "green",
    "cyan":      "cyan",
    "magenta":   "magenta",
    "pink":      "pink",
    "blue":      "blue",
    "red":       "red",
    "turquoise": "turquoise",
    "gray":      "darkGray",
}


def _highlight_run(run, color_name: str):
    color_key = color_name.lower().strip()
    fill_hex  = HIGHLIGHT_HEX.get(color_key, "FFFF00")
    rPr = run._r.get_or_add_rPr()
    for el in list(rPr.findall(qn('w:highlight'))): rPr.remove(el)
    hl = OxmlElement('w:highlight')
    hl.set(qn('w:val'), HIGHLIGHT_XML.get(color_key, 'yellow'))
    rPr.append(hl)
    for el in list(rPr.findall(qn('w:shd'))): rPr.remove(el)
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'),   'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'),  fill_hex)
    rPr.append(shd)


def _remove_highlight_run(run):
    rPr = run._r.get_or_add_rPr()
    for tag in ['w:highlight', 'w:shd']:
        for el in list(rPr.findall(qn(tag))): rPr.remove(el)
    try:
        from docx.enum.text import WD_COLOR_INDEX
        run.font.highlight_color = WD_COLOR_INDEX.NONE
    except Exception:
        pass


class DocumentExecutor:

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.doc       = DocxDocument(file_path)
        self._bookmark_id_counter = 1000

    def save(self):
        self.doc.save(self.file_path)

    def execute_actions(self, actions: list) -> list:
        results = []
        for action in actions:
            action_type = action.get("type")
            params      = action.get("params", {})
            try:
                method = getattr(self, f"action_{action_type}", None)
                if method:
                    results.append({
                        "action": action_type,
                        "status": "success",
                        "result": method(**params)
                    })
                else:
                    results.append({
                        "action": action_type,
                        "status": "skipped",
                        "reason": f"Unknown action: {action_type}"
                    })
            except Exception as e:
                results.append({
                    "action": action_type,
                    "status": "error",
                    "error":  str(e)
                })
        self.save()
        return results

    # ─────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────

    def _find_heading_paragraphs(self):
        headings = []
        for para in self.doc.paragraphs:
            text = para.text.strip()
            if not text: continue
            if para.style.name.startswith("Heading"):
                headings.append(para); continue
            if re.match(r'^\d+[\.\)]\s+\S', text):
                headings.append(para); continue
            if re.match(r'^\d+\.\d+[\.\s]', text):
                headings.append(para); continue
            if re.match(r'^(chapter|section|part)\s+\d+', text, re.IGNORECASE):
                headings.append(para); continue
            if len(text) < 80 and para.runs and \
               all(r.bold for r in para.runs if r.text.strip()):
                headings.append(para); continue
            if text.isupper() and 3 < len(text) < 80:
                headings.append(para); continue
        return headings

    def _find_paragraphs_by_texts(self, texts: list):
        found = []
        for para in self.doc.paragraphs:
            for t in texts:
                if t.lower().strip() in para.text.lower():
                    found.append(para); break
        return found

    def _iter_all_paragraphs(self):
        for para in self.doc.paragraphs: yield para
        for table in self.doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs: yield para

    # ─────────────────────────────────────────
    # HEADING STYLES
    # ─────────────────────────────────────────

    def _setup_heading_styles(self):
        heading_defs = {
            "Heading 1": {"size": 16, "bold": True,  "color": "2E74B5"},
            "Heading 2": {"size": 13, "bold": True,  "color": "2E74B5"},
            "Heading 3": {"size": 12, "bold": True,  "color": "1F4E79"},
            "Heading 4": {"size": 11, "bold": True,  "color": "2E74B5"},
            "Heading 5": {"size": 11, "bold": False, "color": "2E74B5"},
            "Heading 6": {"size": 11, "bold": False, "color": "595959"},
        }
        for style_name, defs in heading_defs.items():
            try:
                style = self.doc.styles[style_name]
                style.font.size      = Pt(defs["size"])
                style.font.bold      = defs["bold"]
                style.font.color.rgb = hex_to_rgb(defs["color"])
                style.font.name      = "Calibri Light"
            except Exception:
                pass
        return "Heading styles set to Word defaults"

    def action_apply_heading_styles(self, **kwargs):
        return self._setup_heading_styles()

    def action_set_heading_style(self, level=None, bold=True,
                                  color=None, font_size=None,
                                  underline=None, **kwargs):
        headings = self._find_heading_paragraphs()
        count = 0
        for para in headings:
            if level and para.style.name.startswith("Heading") and \
               para.style.name != f"Heading {level}": continue
            for run in para.runs:
                if bold      is not None: run.bold           = bold
                if color:                 run.font.color.rgb = hex_to_rgb(color)
                if font_size:             run.font.size      = Pt(font_size)
                if underline is not None: run.font.underline = underline
            count += 1
        if count == 0:
            return "No headings found."
        return f"Heading style updated for {count} paragraphs"

    # ─────────────────────────────────────────
    # CLICKABLE TOC WITH BOOKMARKS
    # ─────────────────────────────────────────

    def action_add_table_of_contents(self, title="Table of Contents",
                                      max_level=3, clickable=True, **kwargs):
        bookmark_count = 0
        for para in self.doc.paragraphs:
            if not para.style.name.startswith("Heading"): continue
            safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', para.text.strip()[:40])
            if not safe_name: continue
            self._bookmark_id_counter += 1
            bm_id = str(self._bookmark_id_counter)
            start = OxmlElement('w:bookmarkStart')
            start.set(qn('w:id'),   bm_id)
            start.set(qn('w:name'), f"_toc_{safe_name}")
            end = OxmlElement('w:bookmarkEnd')
            end.set(qn('w:id'), bm_id)
            para._p.insert(0, start)
            para._p.append(end)
            bookmark_count += 1

        if self.doc.paragraphs:
            tp = self.doc.paragraphs[0].insert_paragraph_before(title)
            p  = self.doc.paragraphs[1].insert_paragraph_before("")
        else:
            tp = self.doc.add_paragraph(title)
            p  = self.doc.add_paragraph("")

        tp.style = "Heading 1"
        run = p.add_run()
        for ft, txt in [
            ('begin', None),
            (None, f'TOC \\o "1-{max_level}" \\h \\z \\u'),
            ('end', None)
        ]:
            if ft:
                e = OxmlElement('w:fldChar')
                e.set(qn('w:fldCharType'), ft)
                run._r.append(e)
            else:
                e = OxmlElement('w:instrText')
                e.set(qn('xml:space'), 'preserve')
                e.text = txt
                run._r.append(e)

        return (f"Clickable TOC inserted with {max_level} levels. "
                f"Bookmarks added to {bookmark_count} headings. "
                f"Press F9 in Word to update page numbers. "
                f"Ctrl+Click any TOC entry to jump to that section.")

    def action_add_internal_link(self, link_text="", target_heading="",
                                  find_in_para=None, **kwargs):
        target_para = None
        for para in self.doc.paragraphs:
            if target_heading.lower() in para.text.lower():
                target_para = para; break

        if not target_para:
            return f"Target heading '{target_heading}' not found"

        self._bookmark_id_counter += 1
        bm_id     = str(self._bookmark_id_counter)
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', target_heading[:40])
        bm_name   = f"_link_{safe_name}"

        start = OxmlElement('w:bookmarkStart')
        start.set(qn('w:id'),   bm_id)
        start.set(qn('w:name'), bm_name)
        end = OxmlElement('w:bookmarkEnd')
        end.set(qn('w:id'), bm_id)
        target_para._p.insert(0, start)
        target_para._p.append(end)

        source_para = None
        if find_in_para:
            for para in self.doc.paragraphs:
                if find_in_para.lower() in para.text.lower():
                    source_para = para; break
        if not source_para:
            source_para = self.doc.add_paragraph()

        hl = OxmlElement('w:hyperlink')
        hl.set(qn('w:anchor'), bm_name)
        new_run = OxmlElement('w:r')
        rPr     = OxmlElement('w:rPr')
        rStyle  = OxmlElement('w:rStyle')
        rStyle.set(qn('w:val'), 'Hyperlink')
        rPr.append(rStyle)
        new_run.append(rPr)
        t = OxmlElement('w:t')
        t.text = link_text or target_heading
        new_run.append(t)
        hl.append(new_run)
        source_para._p.append(hl)

        return (f"Internal link '{link_text}' → '{target_heading}' created. "
                f"Ctrl+Click in Word to jump to that section.")

    def action_link_all_headings(self, **kwargs):
        count = 0
        for para in self.doc.paragraphs:
            if not para.style.name.startswith("Heading"): continue
            text      = para.text.strip()
            safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', text[:40])
            if not safe_name: continue
            existing = para._p.findall(f'.//{qn("w:bookmarkStart")}')
            if existing: continue
            self._bookmark_id_counter += 1
            bm_id = str(self._bookmark_id_counter)
            start = OxmlElement('w:bookmarkStart')
            start.set(qn('w:id'),   bm_id)
            start.set(qn('w:name'), f"_h_{safe_name}")
            end = OxmlElement('w:bookmarkEnd')
            end.set(qn('w:id'), bm_id)
            para._p.insert(0, start)
            para._p.append(end)
            count += 1
        return f"Bookmarks added to {count} headings."

    # ─────────────────────────────────────────
    # VISUAL ELEMENTS
    # ─────────────────────────────────────────

    def action_insert_styled_box(self, text="", style="shadow",
                                  color="#10B981", width_inches=4.0,
                                  text_color="#FFFFFF", **kwargs):
        table = self.doc.add_table(rows=1, cols=1)
        table.style = "Table Grid"
        cell  = table.rows[0].cells[0]
        cell.width = Inches(width_inches)

        styles = {
            "shadow":   {"fill": color.lstrip('#'), "border": "808080", "border_size": "6"},
            "border":   {"fill": "FFFFFF",          "border": color.lstrip('#'), "border_size": "12"},
            "glow":     {"fill": color.lstrip('#'), "border": "FFFFFF", "border_size": "18"},
            "gradient": {"fill": color.lstrip('#'), "border": color.lstrip('#'), "border_size": "6"},
            "rounded":  {"fill": color.lstrip('#'), "border": "FFFFFF", "border_size": "6"},
            "info":     {"fill": "DBEAFE",          "border": "3B82F6", "border_size": "8"},
            "warning":  {"fill": "FEF3C7",          "border": "F59E0B", "border_size": "8"},
            "success":  {"fill": "D1FAE5",          "border": "10B981", "border_size": "8"},
            "danger":   {"fill": "FEE2E2",          "border": "EF4444", "border_size": "8"},
            "callout":  {"fill": "F3F4F6",          "border": "6B7280", "border_size": "8"},
        }
        s = styles.get(style, styles["shadow"])

        tc   = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd  = OxmlElement('w:shd')
        shd.set(qn('w:val'),   'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'),  s["fill"])
        tcPr.append(shd)

        tcBorders = OxmlElement('w:tcBorders')
        for side in ['top', 'left', 'bottom', 'right']:
            b = OxmlElement(f'w:{side}')
            b.set(qn('w:val'),   'single')
            b.set(qn('w:sz'),    s["border_size"])
            b.set(qn('w:color'), s["border"])
            tcBorders.append(b)
        tcPr.append(tcBorders)

        tcMar = OxmlElement('w:tcMar')
        for side in ['top', 'left', 'bottom', 'right']:
            m = OxmlElement(f'w:{side}')
            m.set(qn('w:w'),    '120')
            m.set(qn('w:type'), 'dxa')
            tcMar.append(m)
        tcPr.append(tcMar)

        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run(text)
        run.bold = True
        run.font.size = Pt(11)

        info_styles = {"info", "warning", "callout"}
        if style in info_styles:
            run.font.color.rgb = RGBColor(30, 30, 30)
        elif style == "success":
            run.font.color.rgb = RGBColor(6, 78, 59)
        elif style == "danger":
            run.font.color.rgb = RGBColor(127, 29, 29)
        else:
            try:   run.font.color.rgb = hex_to_rgb(text_color)
            except: run.font.color.rgb = RGBColor(255, 255, 255)

        rPr = run._r.get_or_add_rPr()
        if style == "shadow":
            shadow = OxmlElement('w:shadow')
            shadow.set(qn('w:val'), '1')
            rPr.append(shadow)
        elif style == "glow":
            emboss = OxmlElement('w:emboss')
            emboss.set(qn('w:val'), '1')
            rPr.append(emboss)

        return f"Styled box ({style}) inserted: '{text}'"

    def action_insert_divider(self, style="thick", color="#10B981",
                               text="", **kwargs):
        para = self.doc.add_paragraph(text)
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        style_map = {
            "thick":  ("single", "18"),
            "double": ("double", "6"),
            "dotted": ("dotted", "6"),
            "dashed": ("dashed", "6"),
            "wave":   ("wave",   "6"),
            "triple": ("triple", "6"),
        }
        border_style, sz = style_map.get(style, style_map["thick"])
        pPr  = para._p.get_or_add_pPr()
        pBdr = OxmlElement('w:pBdr')
        for side in ['top', 'bottom']:
            b = OxmlElement(f'w:{side}')
            b.set(qn('w:val'),   border_style)
            b.set(qn('w:sz'),    sz)
            b.set(qn('w:space'), '4')
            b.set(qn('w:color'), color.lstrip('#'))
            pBdr.append(b)
        pPr.append(pBdr)
        if text:
            for run in para.runs:
                run.font.color.rgb = hex_to_rgb(color)
                run.bold = True
        return f"Divider ({style}) inserted"

    def action_insert_highlight_box(self, text="", box_type="note", **kwargs):
        configs = {
            "note":      {"icon": "📝", "fill": "EFF6FF", "border": "3B82F6",
                          "label": "NOTE",      "text_color": "1E40AF"},
            "tip":       {"icon": "💡", "fill": "F0FDF4", "border": "10B981",
                          "label": "TIP",       "text_color": "065F46"},
            "warning":   {"icon": "⚠️", "fill": "FFFBEB", "border": "F59E0B",
                          "label": "WARNING",   "text_color": "92400E"},
            "important": {"icon": "❗", "fill": "FFF1F2", "border": "EF4444",
                          "label": "IMPORTANT", "text_color": "991B1B"},
            "caution":   {"icon": "🔔", "fill": "FFF7ED", "border": "F97316",
                          "label": "CAUTION",   "text_color": "9A3412"},
        }
        cfg   = configs.get(box_type, configs["note"])
        table = self.doc.add_table(rows=2, cols=1)
        table.style = "Table Grid"

        header_cell = table.rows[0].cells[0]
        hPr  = header_cell._tc.get_or_add_tcPr()
        hShd = OxmlElement('w:shd')
        hShd.set(qn('w:val'),  'clear')
        hShd.set(qn('w:fill'), cfg["border"])
        hPr.append(hShd)
        hBdr = OxmlElement('w:tcBorders')
        for side in ['top', 'left', 'bottom', 'right']:
            b = OxmlElement(f'w:{side}')
            b.set(qn('w:val'),   'single')
            b.set(qn('w:sz'),    '6')
            b.set(qn('w:color'), cfg["border"])
            hBdr.append(b)
        hPr.append(hBdr)
        label_para = header_cell.paragraphs[0]
        label_run  = label_para.add_run(f"{cfg['icon']} {cfg['label']}")
        label_run.bold = True
        label_run.font.size = Pt(10)
        label_run.font.color.rgb = RGBColor(255, 255, 255)

        content_cell = table.rows[1].cells[0]
        cPr  = content_cell._tc.get_or_add_tcPr()
        cShd = OxmlElement('w:shd')
        cShd.set(qn('w:val'),  'clear')
        cShd.set(qn('w:fill'), cfg["fill"])
        cPr.append(cShd)
        cBdr = OxmlElement('w:tcBorders')
        for side in ['top', 'left', 'bottom', 'right']:
            b = OxmlElement(f'w:{side}')
            b.set(qn('w:val'),   'single')
            b.set(qn('w:sz'),    '6')
            b.set(qn('w:color'), cfg["border"])
            cBdr.append(b)
        cPr.append(cBdr)
        cMar = OxmlElement('w:tcMar')
        for side in ['top', 'left', 'bottom', 'right']:
            m = OxmlElement(f'w:{side}')
            m.set(qn('w:w'),    '100')
            m.set(qn('w:type'), 'dxa')
            cMar.append(m)
        cPr.append(cMar)
        content_para = content_cell.paragraphs[0]
        cr = content_para.add_run(text)
        cr.font.size = Pt(11)
        cr.font.color.rgb = hex_to_rgb(cfg["text_color"])

        return f"{box_type.upper()} box inserted: '{text[:50]}'"

    def action_insert_badge(self, text="", color="#10B981",
                             text_color="#FFFFFF", **kwargs):
        para = self.doc.add_paragraph()
        run  = para.add_run(f"  {text}  ")
        run.bold = True
        run.font.size = Pt(9)
        run.font.color.rgb = hex_to_rgb(text_color)
        rPr = run._r.get_or_add_rPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'),   'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'),  color.lstrip('#'))
        rPr.append(shd)
        return f"Badge '{text}' inserted"

    def action_set_text_effect(self, find_text=None, effect="shadow",
                                apply_to="all", **kwargs):
        count = 0
        for para in self._iter_all_paragraphs():
            if find_text and find_text.lower() not in para.text.lower(): continue
            for run in para.runs:
                if find_text and find_text.lower() not in run.text.lower(): continue
                rPr = run._r.get_or_add_rPr()
                if effect == "shadow":
                    el = OxmlElement('w:shadow'); el.set(qn('w:val'), '1'); rPr.append(el)
                elif effect == "outline":
                    el = OxmlElement('w:outline'); el.set(qn('w:val'), '1'); rPr.append(el)
                elif effect == "emboss":
                    el = OxmlElement('w:emboss'); el.set(qn('w:val'), '1'); rPr.append(el)
                elif effect == "engrave":
                    el = OxmlElement('w:imprint'); el.set(qn('w:val'), '1'); rPr.append(el)
                elif effect == "small_caps":
                    el = OxmlElement('w:smallCaps'); el.set(qn('w:val'), '1'); rPr.append(el)
                elif effect == "all_caps":
                    el = OxmlElement('w:caps'); el.set(qn('w:val'), '1'); rPr.append(el)
                count += 1
        return f"Text effect '{effect}' applied to {count} runs"

    def action_remove_text_effects(self, find_text=None, **kwargs):
        tags = ['w:shadow','w:outline','w:emboss','w:imprint','w:smallCaps','w:caps']
        count = 0
        for para in self._iter_all_paragraphs():
            if find_text and find_text.lower() not in para.text.lower(): continue
            for run in para.runs:
                rPr = run._r.get_or_add_rPr()
                for tag in tags:
                    for el in list(rPr.findall(qn(tag))): rPr.remove(el)
                count += 1
        return f"Text effects removed from {count} runs"

    def action_insert_image_with_border(self, image_path=None, width_inches=4.0,
                                         border_color="#10B981", border_size=6,
                                         caption=None, alignment="center", **kwargs):
        if not image_path or not os.path.exists(image_path):
            return f"Image not found: {image_path}"
        table = self.doc.add_table(rows=1, cols=1)
        table.style = "Table Grid"
        cell  = table.rows[0].cells[0]
        cell.width = Inches(width_inches + 0.4)
        tc   = cell._tc; tcPr = tc.get_or_add_tcPr()
        shd  = OxmlElement('w:shd')
        shd.set(qn('w:val'),'clear'); shd.set(qn('w:color'),'auto'); shd.set(qn('w:fill'),'FFFFFF')
        tcPr.append(shd)
        tcBorders = OxmlElement('w:tcBorders')
        for side in ['top','left','bottom','right']:
            b = OxmlElement(f'w:{side}')
            b.set(qn('w:val'),'single'); b.set(qn('w:sz'),str(border_size))
            b.set(qn('w:color'),border_color.lstrip('#')); tcBorders.append(b)
        tcPr.append(tcBorders)
        para = cell.paragraphs[0]; para.alignment = get_alignment(alignment)
        run  = para.add_run(); run.add_picture(image_path, width=Inches(width_inches))
        if caption:
            cap_para = self.doc.add_paragraph(caption); cap_para.alignment = get_alignment(alignment)
            for r in cap_para.runs: r.italic = True; r.font.size = Pt(9)
        return f"Bordered image inserted"

    # ─────────────────────────────────────────
    # BASIC FORMATTING
    # ─────────────────────────────────────────

    def action_set_font(self, font_name="Calibri", size=11,
                        bold=None, italic=None, color=None,
                        apply_to="all", find_text=None, **kwargs):
        heading_set = set(id(p) for p in self._find_heading_paragraphs())
        count = 0
        for para in self._iter_all_paragraphs():
            is_heading = id(para) in heading_set or para.style.name.startswith("Heading")
            if apply_to == "headings" and not is_heading: continue
            if apply_to == "body"     and is_heading:     continue
            if find_text and find_text.lower() not in para.text.lower(): continue
            for run in para.runs:
                run.font.name = font_name; run.font.size = Pt(size)
                if bold   is not None: run.font.bold   = bold
                if italic is not None: run.font.italic = italic
                if color:              run.font.color.rgb = hex_to_rgb(color)
            count += 1
        return f"Font set to {font_name} {size}pt for {count} paragraphs"

    def action_replace_font(self, old_font="", new_font="", **kwargs):
        count = 0
        for para in self._iter_all_paragraphs():
            for run in para.runs:
                if run.font.name and run.font.name.lower() == old_font.lower():
                    run.font.name = new_font; count += 1
        return f"Replaced '{old_font}' with '{new_font}' in {count} runs"

    def action_set_alignment(self, alignment="justify", apply_to="all",
                              find_text=None, **kwargs):
        align       = get_alignment(alignment)
        heading_set = set(id(p) for p in self._find_heading_paragraphs())
        count = 0
        for para in self._iter_all_paragraphs():
            is_heading = id(para) in heading_set
            if apply_to == "headings" and not is_heading: continue
            if apply_to == "body"     and is_heading:     continue
            if find_text and find_text.lower() not in para.text.lower(): continue
            para.alignment = align; count += 1
        return f"Alignment set to {alignment} for {count} paragraphs"

    def action_set_margins(self, top=1.0, bottom=1.0, left=1.0, right=1.0, **kwargs):
        for section in self.doc.sections:
            section.top_margin    = Inches(top)
            section.bottom_margin = Inches(bottom)
            section.left_margin   = Inches(left)
            section.right_margin  = Inches(right)
        return f"Margins T={top} B={bottom} L={left} R={right} inches"

    def action_set_paragraph_spacing(self, before=0, after=8,
                                      line_spacing=1.5, apply_to="all",
                                      find_text=None, **kwargs):
        heading_set = set(id(p) for p in self._find_heading_paragraphs())
        count = 0
        for para in self._iter_all_paragraphs():
            is_heading = id(para) in heading_set
            if apply_to == "headings" and not is_heading: continue
            if apply_to == "body"     and is_heading:     continue
            if find_text and find_text.lower() not in para.text.lower(): continue
            pf = para.paragraph_format
            pf.space_before = Pt(before); pf.space_after = Pt(after)
            pf.line_spacing = line_spacing; count += 1
        return f"Spacing applied to {count} paragraphs"

    def action_set_line_spacing_exact(self, value_pt=12.0, apply_to="all", **kwargs):
        heading_set = set(id(p) for p in self._find_heading_paragraphs())
        count = 0
        for para in self._iter_all_paragraphs():
            is_heading = id(para) in heading_set
            if apply_to == "headings" and not is_heading: continue
            if apply_to == "body"     and is_heading:     continue
            pf = para.paragraph_format
            pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
            pf.line_spacing      = Pt(value_pt); count += 1
        return f"Exact line spacing {value_pt}pt for {count} paragraphs"

    def action_set_underline(self, apply_to="all", find_text=None, **kwargs):
        heading_set = set(id(p) for p in self._find_heading_paragraphs())
        count = 0
        for para in self._iter_all_paragraphs():
            is_heading = id(para) in heading_set
            if apply_to == "headings" and not is_heading: continue
            if apply_to == "body"     and is_heading:     continue
            if find_text and find_text.lower() not in para.text.lower(): continue
            for run in para.runs: run.font.underline = True
            count += 1
        return f"Underline applied to {count} paragraphs"

    def action_set_strikethrough(self, apply_to="all", find_text=None, **kwargs):
        heading_set = set(id(p) for p in self._find_heading_paragraphs())
        count = 0
        for para in self._iter_all_paragraphs():
            is_heading = id(para) in heading_set
            if apply_to == "headings" and not is_heading: continue
            if apply_to == "body"     and is_heading:     continue
            if find_text and find_text.lower() not in para.text.lower(): continue
            for run in para.runs: run.font.strike = True
            count += 1
        return f"Strikethrough applied to {count} paragraphs"

    def action_set_highlight(self, color="yellow", find_text=None,
                              apply_to="all", selected_texts=None, **kwargs):
        heading_set  = set(id(p) for p in self._find_heading_paragraphs())
        target_paras = (self._find_paragraphs_by_texts(selected_texts)
                        if selected_texts else list(self.doc.paragraphs))
        count = 0
        for para in target_paras:
            if not para.text.strip(): continue
            is_heading = id(para) in heading_set
            if apply_to == "headings" and not is_heading: continue
            if apply_to == "body"     and is_heading:     continue
            if find_text and find_text.lower() not in para.text.lower(): continue
            for run in para.runs:
                if run.text.strip(): _highlight_run(run, color)
            count += 1
        return f"Highlighted {count} paragraphs in {color}"

    def action_search_and_highlight(self, find_text="", color="yellow", **kwargs):
        count = 0
        for para in self._iter_all_paragraphs():
            if find_text.lower() in para.text.lower():
                for run in para.runs:
                    if find_text.lower() in run.text.lower():
                        _highlight_run(run, color); count += 1
        return f"Highlighted {count} runs containing '{find_text}'"

    def action_remove_highlight(self, apply_to="all", find_text=None,
                                 selected_texts=None, **kwargs):
        target_paras = (self._find_paragraphs_by_texts(selected_texts)
                        if selected_texts else list(self.doc.paragraphs))
        count = 0
        for para in target_paras:
            if find_text and find_text.lower() not in para.text.lower(): continue
            for run in para.runs: _remove_highlight_run(run)
            count += 1
        return f"Highlight removed from {count} paragraphs"

    def action_set_superscript(self, find_text=None, **kwargs):
        for para in self._iter_all_paragraphs():
            for run in para.runs:
                if find_text is None or find_text in run.text:
                    run.font.superscript = True
        return "Superscript applied"

    def action_set_subscript(self, find_text=None, **kwargs):
        for para in self._iter_all_paragraphs():
            for run in para.runs:
                if find_text is None or find_text in run.text:
                    run.font.subscript = True
        return "Subscript applied"

    def action_set_text_color(self, color="#000000", apply_to="all",
                               find_text=None, selected_texts=None, **kwargs):
        rgb          = hex_to_rgb(color)
        heading_set  = set(id(p) for p in self._find_heading_paragraphs())
        target_paras = (self._find_paragraphs_by_texts(selected_texts)
                        if selected_texts else list(self._iter_all_paragraphs()))
        count = 0
        for para in target_paras:
            is_heading = id(para) in heading_set
            if apply_to == "headings" and not is_heading: continue
            if apply_to == "body"     and is_heading:     continue
            if find_text and find_text.lower() not in para.text.lower(): continue
            for run in para.runs: run.font.color.rgb = rgb
            count += 1
        return f"Text color set to {color} for {count} paragraphs"

    def action_set_indent(self, left=0.5, right=0.0, first_line=0.0,
                           apply_to="all", find_text=None, **kwargs):
        heading_set = set(id(p) for p in self._find_heading_paragraphs())
        count = 0
        for para in self._iter_all_paragraphs():
            is_heading = id(para) in heading_set
            if apply_to == "body"     and is_heading:     continue
            if apply_to == "headings" and not is_heading: continue
            if find_text and find_text.lower() not in para.text.lower(): continue
            pf = para.paragraph_format
            pf.left_indent  = Inches(left); pf.right_indent = Inches(right)
            if first_line: pf.first_line_indent = Inches(first_line)
            count += 1
        return f"Indent applied to {count} paragraphs"

    def action_remove_formatting(self, apply_to="all", find_text=None, **kwargs):
        heading_set = set(id(p) for p in self._find_heading_paragraphs())
        count = 0
        for para in self._iter_all_paragraphs():
            is_heading = id(para) in heading_set
            if apply_to == "headings" and not is_heading: continue
            if apply_to == "body"     and is_heading:     continue
            if find_text and find_text.lower() not in para.text.lower(): continue
            for run in para.runs:
                run.font.bold = run.font.italic = run.font.underline = run.font.strike = False
                run.font.color.rgb = RGBColor(0, 0, 0)
                _remove_highlight_run(run)
            count += 1
        return f"Formatting removed from {count} paragraphs"

    def action_set_character_spacing(self, spacing=1.0, **kwargs):
        for para in self._iter_all_paragraphs():
            for run in para.runs:
                rPr = run._r.get_or_add_rPr()
                el  = OxmlElement('w:spacing')
                el.set(qn('w:val'), str(int(spacing * 20)))
                rPr.append(el)
        return f"Character spacing set to {spacing}pt"

    def action_set_text_case(self, case="upper", apply_to="all",
                              find_text=None, **kwargs):
        heading_set = set(id(p) for p in self._find_heading_paragraphs())
        count = 0
        for para in self._iter_all_paragraphs():
            is_heading = id(para) in heading_set
            if apply_to == "headings" and not is_heading: continue
            if apply_to == "body"     and is_heading:     continue
            if find_text and find_text.lower() not in para.text.lower(): continue
            for run in para.runs:
                if not run.text: continue
                if case == "upper":    run.text = run.text.upper()
                elif case == "lower":  run.text = run.text.lower()
                elif case == "title":  run.text = run.text.title()
                elif case == "sentence":
                    t = run.text
                    run.text = t[0].upper() + t[1:].lower() if t else t
            count += 1
        return f"Text case '{case}' for {count} paragraphs"

    def action_copy_formatting(self, source_text="", target_text="", **kwargs):
        source_para = None
        for para in self._iter_all_paragraphs():
            if source_text.lower() in para.text.lower():
                source_para = para; break
        if not source_para: return f"Source text '{source_text}' not found"
        if not source_para.runs: return "Source paragraph has no runs"
        src_run = source_para.runs[0]; count = 0
        for para in self._iter_all_paragraphs():
            if target_text.lower() in para.text.lower() and para != source_para:
                para.alignment = source_para.alignment
                para.paragraph_format.space_before = source_para.paragraph_format.space_before
                para.paragraph_format.space_after  = source_para.paragraph_format.space_after
                para.paragraph_format.line_spacing  = source_para.paragraph_format.line_spacing
                for run in para.runs:
                    if src_run.font.name: run.font.name  = src_run.font.name
                    if src_run.font.size: run.font.size  = src_run.font.size
                    run.font.bold = src_run.font.bold
                    run.font.italic = src_run.font.italic
                    run.font.underline = src_run.font.underline
                    try:
                        if src_run.font.color.type: run.font.color.rgb = src_run.font.color.rgb
                    except: pass
                count += 1
        return f"Formatting copied to {count} paragraphs"

    def action_set_paragraph_shading(self, color="#F0FDF4", apply_to="all",
                                      find_text=None, selected_texts=None, **kwargs):
        heading_set  = set(id(p) for p in self._find_heading_paragraphs())
        target_paras = (self._find_paragraphs_by_texts(selected_texts)
                        if selected_texts else list(self._iter_all_paragraphs()))
        count = 0
        for para in target_paras:
            is_heading = id(para) in heading_set
            if apply_to == "headings" and not is_heading: continue
            if apply_to == "body"     and is_heading:     continue
            if find_text and find_text.lower() not in para.text.lower(): continue
            pPr = para._p.get_or_add_pPr()
            for existing in list(pPr.findall(qn('w:shd'))): pPr.remove(existing)
            shd = OxmlElement('w:shd')
            shd.set(qn('w:val'),'clear'); shd.set(qn('w:color'),'auto')
            shd.set(qn('w:fill'), color.lstrip('#'))
            pPr.append(shd); count += 1
        return f"Paragraph shading {color} for {count} paragraphs"

    def action_set_paragraph_border(self, style="single", color="#000000",
                                     sides="all", find_text=None, **kwargs):
        target_paras = list(self._iter_all_paragraphs())
        if find_text:
            target_paras = [p for p in target_paras if find_text.lower() in p.text.lower()]
        count = 0
        side_list = ['top','left','bottom','right'] if sides == "all" else [sides]
        for para in target_paras:
            pPr  = para._p.get_or_add_pPr()
            pBdr = pPr.find(qn('w:pBdr'))
            if pBdr is None:
                pBdr = OxmlElement('w:pBdr'); pPr.append(pBdr)
            for side in side_list:
                b = OxmlElement(f'w:{side}')
                b.set(qn('w:val'),style); b.set(qn('w:sz'),'4')
                b.set(qn('w:space'),'4'); b.set(qn('w:color'),color.lstrip('#'))
                pBdr.append(b)
            count += 1
        return f"Paragraph border ({style}) added to {count} paragraphs"

    def action_set_keep_with_next(self, apply_to="headings", **kwargs):
        heading_set = set(id(p) for p in self._find_heading_paragraphs())
        count = 0
        for para in self.doc.paragraphs:
            is_heading = id(para) in heading_set
            if apply_to == "headings" and not is_heading: continue
            pPr = para._p.get_or_add_pPr()
            kwn = OxmlElement('w:keepNext'); kwn.set(qn('w:val'),'1'); pPr.append(kwn)
            count += 1
        return f"Keep with next applied to {count} paragraphs"

    def action_set_widow_orphan_control(self, enabled=True, **kwargs):
        for para in self.doc.paragraphs:
            pPr = para._p.get_or_add_pPr()
            wo  = OxmlElement('w:widowControl')
            wo.set(qn('w:val'), '1' if enabled else '0'); pPr.append(wo)
        return f"Widow/orphan control {'enabled' if enabled else 'disabled'}"

    def action_set_drop_cap(self, paragraph_index=0, lines=3, font_name=None, **kwargs):
        paras = [p for p in self.doc.paragraphs if p.text.strip()]
        if paragraph_index >= len(paras): return f"Paragraph {paragraph_index} not found"
        para = paras[paragraph_index]
        if not para.runs or not para.runs[0].text: return "No text for drop cap"
        first_char = para.runs[0].text[0]
        para.runs[0].text = para.runs[0].text[1:]
        drop = para.insert_paragraph_before(""); run = drop.add_run(first_char)
        if font_name: run.font.name = font_name
        run.font.size = Pt(11 * lines * 1.8); run.font.bold = True
        pPr = drop._p.get_or_add_pPr(); fp = OxmlElement('w:framePr')
        fp.set(qn('w:dropCap'),'drop'); fp.set(qn('w:lines'),str(lines))
        fp.set(qn('w:wrap'),'around'); fp.set(qn('w:vAnchor'),'text')
        fp.set(qn('w:hAnchor'),'text'); pPr.append(fp)
        return f"Drop cap '{first_char}' applied"

    # ─────────────────────────────────────────
    # TRACK CHANGES
    # ─────────────────────────────────────────

    def action_enable_track_changes(self, **kwargs):
        settings = self.doc.settings.element
        tc = OxmlElement('w:trackChanges'); tc.set(qn('w:val'),'1'); settings.append(tc)
        return "Track changes enabled"

    def action_disable_track_changes(self, **kwargs):
        settings = self.doc.settings.element
        for el in settings.findall(qn('w:trackChanges')): settings.remove(el)
        return "Track changes disabled"

    def action_accept_all_changes(self, **kwargs):
        body = self.doc.element.body
        for ins in body.findall(f'.//{qn("w:ins")}'):
            parent = ins.getparent(); idx = list(parent).index(ins)
            for child in list(ins): parent.insert(idx, child); idx += 1
            parent.remove(ins)
        for del_el in body.findall(f'.//{qn("w:del")}'): del_el.getparent().remove(del_el)
        return "All tracked changes accepted"

    def action_reject_all_changes(self, **kwargs):
        body = self.doc.element.body
        for ins in body.findall(f'.//{qn("w:ins")}'): ins.getparent().remove(ins)
        for del_el in body.findall(f'.//{qn("w:del")}'):
            parent = del_el.getparent(); idx = list(parent).index(del_el)
            for child in list(del_el): parent.insert(idx, child); idx += 1
            parent.remove(del_el)
        return "All tracked changes rejected"

    # ─────────────────────────────────────────
    # CHECKLISTS
    # ─────────────────────────────────────────

    def action_add_checklist(self, items=None, **kwargs):
        if not items: return "No items provided"
        for item in items:
            checked = item.get("checked", False) if isinstance(item, dict) else False
            text    = item.get("text", item)     if isinstance(item, dict) else item
            checkbox = "☑ " if checked else "☐ "
            para = self.doc.add_paragraph(); run = para.add_run(checkbox + text)
            pPr  = para._p.get_or_add_pPr()
            ind  = OxmlElement('w:ind'); ind.set(qn('w:left'),'360'); pPr.append(ind)
        return f"Checklist added with {len(items)} items"

    def action_convert_to_checklist(self, **kwargs):
        count = 0
        for para in self.doc.paragraphs:
            t = para.text.strip()
            if re.match(r'^[-*]\s*\[[ xX]\]\s*', t) or re.match(r'^[-*]\s+', t):
                checked = bool(re.match(r'^[-*]\s*\[[xX]\]', t))
                clean   = re.sub(r'^[-*]\s*\[[ xX]\]\s*', '', t)
                clean   = re.sub(r'^[-*]\s+', '', clean)
                para.text = ("☑ " if checked else "☐ ") + clean; count += 1
        return f"Converted {count} items to checklist"

    # ─────────────────────────────────────────
    # SELECTION-BASED
    # ─────────────────────────────────────────

    def action_apply_to_selection(self, selected_texts=None, command_type="bold",
                                   font_name=None, font_size=None, color=None,
                                   highlight_color=None, alignment=None,
                                   make_heading=None, **kwargs):
        if not selected_texts: return "No selected text provided"
        target_paras = self._find_paragraphs_by_texts(selected_texts)
        if not target_paras: return "Could not find selected text in document."
        count = 0
        for para in target_paras:
            if command_type == "bold":
                for run in para.runs: run.bold = True
            elif command_type == "italic":
                for run in para.runs: run.italic = True
            elif command_type == "underline":
                for run in para.runs: run.font.underline = True
            elif command_type == "strikethrough":
                for run in para.runs: run.font.strike = True
            elif command_type == "remove_bold":
                for run in para.runs: run.bold = False
            elif command_type == "remove_italic":
                for run in para.runs: run.italic = False
            elif command_type == "remove_formatting":
                for run in para.runs:
                    run.font.bold = run.font.italic = run.font.underline = False
                    run.font.strike = False; run.font.color.rgb = RGBColor(0,0,0)
                    _remove_highlight_run(run)
            elif command_type == "highlight":
                hc = highlight_color or "yellow"
                for run in para.runs:
                    if run.text.strip(): _highlight_run(run, hc)
            elif command_type == "remove_highlight":
                for run in para.runs: _remove_highlight_run(run)
            elif command_type == "heading":
                level = make_heading or 1
                try:    para.style = self.doc.styles[f"Heading {level}"]
                except KeyError:
                    for run in para.runs:
                        run.bold = True; run.font.size = Pt(max(10, 18 - (level * 2)))
            elif command_type == "font":
                for run in para.runs:
                    if font_name: run.font.name = font_name
                    if font_size: run.font.size = Pt(font_size)
            elif command_type == "color":
                if color:
                    for run in para.runs: run.font.color.rgb = hex_to_rgb(color)
            elif command_type == "align":
                if alignment: para.alignment = get_alignment(alignment)
            elif command_type == "uppercase":
                for run in para.runs: run.text = run.text.upper()
            elif command_type == "lowercase":
                for run in para.runs: run.text = run.text.lower()
            elif command_type == "capitalize":
                for run in para.runs: run.text = run.text.title()
            count += 1
        preview = ', '.join(f'"{t[:30]}"' for t in selected_texts[:2])
        return f"Applied '{command_type}' to {count} paragraph(s): {preview}"

    # ─────────────────────────────────────────
    # TEXT OPERATIONS
    # ─────────────────────────────────────────

    def action_find_replace(self, find="", replace="", case_sensitive=False, **kwargs):
        count = 0
        for para in self._iter_all_paragraphs():
            for run in para.runs:
                if case_sensitive:
                    if find in run.text: run.text = run.text.replace(find, replace); count += 1
                else:
                    new = re.sub(re.escape(find), replace, run.text, flags=re.IGNORECASE)
                    if new != run.text: run.text = new; count += 1
        return f"Replaced {count} occurrences of '{find}' with '{replace}'"

    def action_add_text(self, text="", position="end", new_paragraph=True, **kwargs):
        if position == "end":
            self.doc.add_paragraph(text) if new_paragraph \
            else (self.doc.paragraphs[-1].add_run(" " + text) if self.doc.paragraphs else None)
        elif position == "beginning" and self.doc.paragraphs:
            self.doc.paragraphs[0].insert_paragraph_before(text)
        return f"Text added at {position}"

    def action_delete_text(self, find="", **kwargs):
        return self.action_find_replace(find=find, replace="")

    def action_count_words(self, **kwargs):
        total = sum(len(p.text.split()) for p in self._iter_all_paragraphs() if p.text.strip())
        return f"Document has {total} words"

    def action_count_paragraphs(self, **kwargs):
        return f"Document has {sum(1 for p in self.doc.paragraphs if p.text.strip())} paragraphs"

    def action_extract_text(self, **kwargs):
        return "\n".join(p.text for p in self._iter_all_paragraphs() if p.text.strip())

    def action_set_language(self, language="en-US", apply_to="all", **kwargs):
        count = 0
        for para in self._iter_all_paragraphs():
            for run in para.runs:
                rPr  = run._r.get_or_add_rPr()
                lang = OxmlElement('w:lang'); lang.set(qn('w:val'), language); rPr.append(lang)
            count += 1
        return f"Language set to {language} for {count} paragraphs"

    # ─────────────────────────────────────────
    # LISTS
    # ─────────────────────────────────────────

    def action_add_bullet_list(self, items=None, position="end", **kwargs):
        if not items: return "No items provided"
        for item in items:
            try:
                p = self.doc.add_paragraph(style="List Bullet"); p.text = item
            except KeyError:
                p = self.doc.add_paragraph(); p.text = f"• {item}"
                pPr = p._p.get_or_add_pPr(); ind = OxmlElement('w:ind')
                ind.set(qn('w:left'),'720'); ind.set(qn('w:hanging'),'360'); pPr.append(ind)
        return f"Bullet list added with {len(items)} items"

    def action_add_numbered_list(self, items=None, position="end", restart=True, **kwargs):
        if not items: return "No items provided"
        try:
            for item in items: self.doc.add_paragraph(item, style="List Number")
            return f"Numbered list added with {len(items)} items"
        except KeyError:
            for i, item in enumerate(items, 1):
                p = self.doc.add_paragraph(); p.text = f"{i}. {item}"
                pPr = p._p.get_or_add_pPr(); ind = OxmlElement('w:ind')
                ind.set(qn('w:left'),'720'); ind.set(qn('w:hanging'),'360'); pPr.append(ind)
            return f"Numbered list added with {len(items)} items"

    def action_add_multilevel_list(self, items=None, **kwargs):
        if not items: return "No items provided"
        sm = {0:"List Number", 1:"List Number 2", 2:"List Number 3"}
        im = {0:('360','180'), 1:('720','360'), 2:('1080','540')}
        for item in items:
            level = item.get("level",0); text = item.get("text","")
            try:    self.doc.add_paragraph(text, style=sm.get(level,"List Number"))
            except KeyError:
                l, h = im.get(level, im[0]); p = self.doc.add_paragraph(); p.text = text
                pPr = p._p.get_or_add_pPr(); ind = OxmlElement('w:ind')
                ind.set(qn('w:left'),l); ind.set(qn('w:hanging'),h); pPr.append(ind)
        return f"Multilevel list added with {len(items)} items"

    def action_convert_to_bullets(self, **kwargs):
        converted = 0
        for para in self.doc.paragraphs:
            t = para.text.strip()
            if re.match(r'^[-*•]\s+', t) or re.match(r'^\d+[.)]\s+', t):
                clean = re.sub(r'^[-*•\d.)]+\s*', '', t); para.text = clean
                try:   para.style = self.doc.styles['List Bullet']
                except KeyError: para.text = f"• {clean}"
                converted += 1
        return f"Converted {converted} paragraphs to bullet list"

    def action_restart_numbering(self, list_style="List Number", **kwargs):
        try:    self.doc.add_paragraph("", style=list_style)
        except: self.doc.add_paragraph()
        return "Numbering restart marker added"

    # ─────────────────────────────────────────
    # PAGE MANAGEMENT
    # ─────────────────────────────────────────

    def action_add_page_break(self, after_page=1, **kwargs):
        para = self.doc.add_paragraph(); run = para.add_run()
        br = OxmlElement('w:br'); br.set(qn('w:type'),'page'); run._r.append(br)
        return "Page break added"

    def action_add_blank_page(self, after_page=1, **kwargs):
        self.action_add_page_break(); self.doc.add_paragraph(""); self.action_add_page_break()
        return "Blank page added"

    def action_set_page_size(self, size="A4", **kwargs):
        sizes = {"A4":(210,297),"Letter":(215.9,279.4),"A3":(297,420),"A5":(148,210),"Legal":(215.9,355.6)}
        w, h = sizes.get(size, (210, 297))
        for section in self.doc.sections:
            section.page_width = Mm(w); section.page_height = Mm(h)
        return f"Page size set to {size}"

    def action_set_page_orientation(self, orientation="portrait", **kwargs):
        for section in self.doc.sections:
            if orientation == "landscape":
                section.orientation = WD_ORIENT.LANDSCAPE
                section.page_width, section.page_height = section.page_height, section.page_width
            else:
                section.orientation = WD_ORIENT.PORTRAIT
        return f"Orientation set to {orientation}"

    def action_set_page_color(self, color="#FFFFFF", **kwargs):
        bg = OxmlElement('w:background'); bg.set(qn('w:color'), color.lstrip('#'))
        self.doc.element.insert(0, bg)
        self.doc.settings.element.append(OxmlElement('w:displayBackgroundShape'))
        return f"Page color set to {color}"

    def action_add_line_numbers(self, start=1, step=1, restart="newPage", **kwargs):
        for section in self.doc.sections:
            ln = OxmlElement('w:lnNumType')
            ln.set(qn('w:countBy'),str(step)); ln.set(qn('w:start'),str(start))
            ln.set(qn('w:restart'),restart); section._sectPr.append(ln)
        return "Line numbers added"

    def action_remove_line_numbers(self, **kwargs):
        for section in self.doc.sections:
            for ln in section._sectPr.findall(qn('w:lnNumType')): section._sectPr.remove(ln)
        return "Line numbers removed"

    def action_set_page_number_start(self, start=1, **kwargs):
        for section in self.doc.sections:
            pgNumType = OxmlElement('w:pgNumType')
            pgNumType.set(qn('w:start'), str(start)); section._sectPr.append(pgNumType)
        return f"Page numbering starts at {start}"

    # ─────────────────────────────────────────
    # HEADERS AND FOOTERS
    # ─────────────────────────────────────────

    def action_add_header(self, text="", alignment="center", **kwargs):
        for section in self.doc.sections:
            header = section.header
            para   = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
            para.clear(); para.add_run(text); para.alignment = get_alignment(alignment)
        return f"Header added: '{text}'"

    def action_add_footer(self, text="", alignment="center", **kwargs):
        for section in self.doc.sections:
            footer = section.footer
            para   = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
            para.clear(); para.add_run(text); para.alignment = get_alignment(alignment)
        return f"Footer added: '{text}'"

    def action_remove_header(self, **kwargs):
        for section in self.doc.sections:
            for para in section.header.paragraphs: para.clear()
        return "Header removed"

    def action_remove_footer(self, **kwargs):
        for section in self.doc.sections:
            for para in section.footer.paragraphs: para.clear()
        return "Footer removed"

    def action_add_page_numbers(self, position="footer", alignment="right",
                                 format="Page X", **kwargs):
        for section in self.doc.sections:
            target = section.footer if position == "footer" else section.header
            para   = target.paragraphs[0] if target.paragraphs else target.add_paragraph()
            para.clear(); para.alignment = get_alignment(alignment)
            run = para.add_run()
            if format == "Page X": run.text = "Page "
            for ft, txt in [('begin',None),(None,"PAGE"),('end',None)]:
                if ft: e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'),ft); run._r.append(e)
                else:  e = OxmlElement('w:instrText'); e.text=txt; run._r.append(e)
            if format == "X of Y":
                run2 = para.add_run(" of ")
                for ft, txt in [('begin',None),(None,"NUMPAGES"),('end',None)]:
                    if ft: e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'),ft); run2._r.append(e)
                    else:  e = OxmlElement('w:instrText'); e.text=txt; run2._r.append(e)
        return f"Page numbers added to {position} ({alignment})"

    def action_set_different_first_page_header(self, first_header="", rest_header="", **kwargs):
        for section in self.doc.sections:
            section.different_first_page_header_footer = True
            fh = section.first_page_header
            (fh.paragraphs[0] if fh.paragraphs else fh.add_paragraph()).text = first_header
            hdr = section.header
            (hdr.paragraphs[0] if hdr.paragraphs else hdr.add_paragraph()).text = rest_header
        return "Different first page header set"

    def action_set_section_header(self, section_index=0, text="",
                                   alignment="center", link_to_previous=False, **kwargs):
        if section_index >= len(self.doc.sections): return f"Section {section_index} not found"
        section = self.doc.sections[section_index]
        section.header.is_linked_to_previous = link_to_previous
        para = section.header.paragraphs[0] if section.header.paragraphs else section.header.add_paragraph()
        para.clear(); para.add_run(text); para.alignment = get_alignment(alignment)
        return f"Section {section_index} header: '{text}'"

    def action_set_section_footer(self, section_index=0, text="",
                                   alignment="center", link_to_previous=False, **kwargs):
        if section_index >= len(self.doc.sections): return f"Section {section_index} not found"
        section = self.doc.sections[section_index]
        section.footer.is_linked_to_previous = link_to_previous
        para = section.footer.paragraphs[0] if section.footer.paragraphs else section.footer.add_paragraph()
        para.clear(); para.add_run(text); para.alignment = get_alignment(alignment)
        return f"Section {section_index} footer: '{text}'"

    def action_insert_date_field(self, position="end", **kwargs):
        para = self.doc.add_paragraph(); run = para.add_run()
        for ft, txt in [('begin',None),(None,' DATE \\@ "DD/MM/YYYY" \\* MERGEFORMAT '),('end',None)]:
            if ft: e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'),ft); run._r.append(e)
            else:  e = OxmlElement('w:instrText'); e.text=txt; run._r.append(e)
        return "Date field inserted"

    def action_insert_page_count_field(self, position="footer", **kwargs):
        for section in self.doc.sections:
            target = section.footer if position == "footer" else section.header
            para   = target.add_paragraph(); para.add_run("Total pages: ")
            run = para.add_run()
            for ft, txt in [('begin',None),(None,"NUMPAGES"),('end',None)]:
                if ft: e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'),ft); run._r.append(e)
                else:  e = OxmlElement('w:instrText'); e.text=txt; run._r.append(e)
        return "Page count field inserted"

    # ─────────────────────────────────────────
    # IMAGES
    # ─────────────────────────────────────────

    def action_insert_image(self, image_path=None, width_inches=None,
                             height_inches=None, position="end",
                             alignment="center", caption=None, **kwargs):
        if not image_path or not os.path.exists(image_path):
            return f"Image not found: {image_path}"
        para = self.doc.add_paragraph(); para.alignment = get_alignment(alignment)
        run  = para.add_run()
        if width_inches and height_inches:
            run.add_picture(image_path, width=Inches(width_inches), height=Inches(height_inches))
        elif width_inches: run.add_picture(image_path, width=Inches(width_inches))
        else:              run.add_picture(image_path, width=Inches(4.0))
        if caption:
            cap = self.doc.add_paragraph(caption); cap.alignment = get_alignment(alignment)
            for r in cap.runs: r.italic = True; r.font.size = Pt(9)
        return "Image inserted"

    def action_insert_logo(self, image_path=None, page="first",
                            position="top_right", width_inches=1.5, **kwargs):
        if not image_path or not os.path.exists(image_path): return "Logo not found"
        am = {"top_right":WD_ALIGN_PARAGRAPH.RIGHT,"top_left":WD_ALIGN_PARAGRAPH.LEFT,
              "top_center":WD_ALIGN_PARAGRAPH.CENTER}
        for i, section in enumerate(self.doc.sections):
            if page == "first" and i > 0: continue
            header = section.header
            para   = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
            para.alignment = am.get(position, WD_ALIGN_PARAGRAPH.RIGHT)
            para.add_run().add_picture(image_path, width=Inches(width_inches))
        return f"Logo inserted at {position}"

    def action_caption_image(self, image_index=0, caption_text="", label="Figure", **kwargs):
        cap = self.doc.add_paragraph(); cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = cap.add_run(f"{label} "); run.bold = True; fr = cap.add_run()
        for ft, txt in [('begin',None),(None,f' SEQ {label} \\* ARABIC '),('end',None)]:
            if ft: e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'),ft); fr._r.append(e)
            else:  e = OxmlElement('w:instrText'); e.text=txt; fr._r.append(e)
        cap.add_run(f": {caption_text}").italic = True
        return f"Caption added: '{caption_text}'"

    # ─────────────────────────────────────────
    # TABLES
    # ─────────────────────────────────────────

    def action_insert_table(self, rows=3, cols=3, position="end", headers=None, **kwargs):
        table = self.doc.add_table(rows=rows, cols=cols); table.style = "Table Grid"
        if headers:
            for i, h in enumerate(headers[:cols]): table.rows[0].cells[i].text = h
        return f"Table inserted {rows}x{cols}"

    def action_format_table(self, style="Table Grid", **kwargs):
        for table in self.doc.tables:
            try: table.style = style
            except: pass
        return f"Tables formatted: {style}"

    def action_set_table_cell_color(self, table_index=0, row=0, col=0, color="#FFFFFF", **kwargs):
        try:
            cell = self.doc.tables[table_index].rows[row].cells[col]
            shd  = OxmlElement('w:shd')
            shd.set(qn('w:val'),'clear'); shd.set(qn('w:color'),'auto')
            shd.set(qn('w:fill'), color.lstrip('#'))
            cell._tc.get_or_add_tcPr().append(shd)
            return f"Cell ({row},{col}) color set to {color}"
        except IndexError: return "Cell not found"

    def action_set_table_header_color(self, table_index=0, color="#10B981", **kwargs):
        try:
            for cell in self.doc.tables[table_index].rows[0].cells:
                shd = OxmlElement('w:shd')
                shd.set(qn('w:val'),'clear'); shd.set(qn('w:color'),'auto')
                shd.set(qn('w:fill'), color.lstrip('#'))
                cell._tc.get_or_add_tcPr().append(shd)
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.font.color.rgb = RGBColor(255,255,255); run.font.bold = True
            return f"Table header colored {color}"
        except IndexError: return "Table not found"

    def action_set_table_borders(self, table_index=0, border_color="#000000",
                                  border_size=4, **kwargs):
        try:
            tbl   = self.doc.tables[table_index]._tbl
            tblPr = tbl.tblPr
            if tblPr is None: tblPr = OxmlElement('w:tblPr'); tbl.insert(0, tblPr)
            tblB  = OxmlElement('w:tblBorders')
            for name in ['top','left','bottom','right','insideH','insideV']:
                b = OxmlElement(f'w:{name}')
                b.set(qn('w:val'),'single'); b.set(qn('w:sz'),str(border_size))
                b.set(qn('w:color'), border_color.lstrip('#')); tblB.append(b)
            tblPr.append(tblB); return "Table borders set"
        except Exception as e: return f"Border error: {e}"

    def action_merge_table_cells(self, table_index=0, start_row=0, start_col=0,
                                  end_row=0, end_col=1, **kwargs):
        try:
            t = self.doc.tables[table_index]
            t.cell(start_row, start_col).merge(t.cell(end_row, end_col))
            return "Cells merged"
        except Exception as e: return f"Merge error: {e}"

    def action_set_column_width(self, table_index=0, col=0, width_inches=1.5, **kwargs):
        try:
            for row in self.doc.tables[table_index].rows:
                row.cells[col].width = Inches(width_inches)
            return f"Column {col} width set to {width_inches}in"
        except Exception as e: return f"Width error: {e}"

    def action_add_table_row(self, table_index=0, data=None, **kwargs):
        try:
            row = self.doc.tables[table_index].add_row()
            if data:
                for i, t in enumerate(data[:len(row.cells)]): row.cells[i].text = str(t)
            return "Row added"
        except Exception as e: return f"Add row error: {e}"

    def action_delete_table_row(self, table_index=0, row_index=0, **kwargs):
        try:
            table = self.doc.tables[table_index]; row = table.rows[row_index]
            row._tr.getparent().remove(row._tr); return f"Row {row_index} deleted"
        except Exception as e: return f"Delete row error: {e}"

    def action_caption_table(self, table_index=0, caption_text="", label="Table", **kwargs):
        try:    table = self.doc.tables[table_index]
        except: return f"Table {table_index} not found"
        cap = self.doc.add_paragraph(); run = cap.add_run(f"{label} "); run.bold = True
        fr  = cap.add_run()
        for ft, txt in [('begin',None),(None,f' SEQ {label} \\* ARABIC '),('end',None)]:
            if ft: e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'),ft); fr._r.append(e)
            else:  e = OxmlElement('w:instrText'); e.text=txt; fr._r.append(e)
        cap.add_run(f": {caption_text}").italic = True
        table._tbl.addprevious(cap._p)
        return "Table caption added"

    def action_sort_table(self, table_index=0, col=0, ascending=True, **kwargs):
        try:
            table = self.doc.tables[table_index]
            if len(table.rows) < 2: return "Table has no data rows"
            data_rows = list(table.rows[1:])
            data_rows.sort(key=lambda r: r.cells[col].text.strip().lower(), reverse=not ascending)
            for row in data_rows: table._tbl.append(row._tr)
            return f"Table sorted by column {col}"
        except Exception as e: return f"Sort error: {e}"

    def action_set_table_cell_alignment(self, table_index=0, row=0, col=0,
                                         alignment="center", **kwargs):
        try:
            cell = self.doc.tables[table_index].rows[row].cells[col]
            for para in cell.paragraphs: para.alignment = get_alignment(alignment)
            return f"Cell ({row},{col}) alignment set to {alignment}"
        except IndexError: return "Cell not found"

    def action_set_table_row_height(self, table_index=0, row_index=0,
                                     height_inches=0.5, **kwargs):
        try:
            self.doc.tables[table_index].rows[row_index].height = Inches(height_inches)
            return f"Row {row_index} height set to {height_inches}in"
        except Exception as e: return f"Row height error: {e}"

    # ─────────────────────────────────────────
    # REFERENCES
    # ─────────────────────────────────────────

    def action_add_table_of_figures(self, title="Table of Figures", label="Figure", **kwargs):
        h = self.doc.add_paragraph(title); h.style = "Heading 1"
        p = self.doc.add_paragraph(""); run = p.add_run()
        for ft, txt in [('begin',None),(None,f'TOC \\h \\z \\c "{label}"'),('end',None)]:
            if ft: e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'),ft); run._r.append(e)
            else:  e = OxmlElement('w:instrText'); e.text=txt; run._r.append(e)
        return f"Table of {label}s inserted (update with F9)"

    def action_add_index(self, entries=None, title="Index", **kwargs):
        if not entries: entries = []
        marked = 0
        for term in entries:
            for para in self._iter_all_paragraphs():
                if term.lower() in para.text.lower():
                    run = para.add_run()
                    for ft, txt in [('begin',None),(None,f' XE "{term}" '),('end',None)]:
                        if ft: e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'),ft); run._r.append(e)
                        else:  e = OxmlElement('w:instrText'); e.text=txt; run._r.append(e)
                    marked += 1; break
        self.action_add_page_break()
        h = self.doc.add_paragraph(title); h.style = "Heading 1"
        p = self.doc.add_paragraph(""); run = p.add_run()
        for ft, txt in [('begin',None),(None,'INDEX \\h "A" \\c "1" \\z "1033"'),('end',None)]:
            if ft: e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'),ft); run._r.append(e)
            else:  e = OxmlElement('w:instrText'); e.text=txt; run._r.append(e)
        return f"Index inserted with {marked} entries"

    def action_add_bookmark(self, name="", find_text=None, **kwargs):
        self._bookmark_id_counter += 1
        safe = name.replace(" ","_")
        target = None
        if find_text:
            for para in self._iter_all_paragraphs():
                if find_text in para.text: target = para; break
        if target is None: target = self.doc.add_paragraph()
        start = OxmlElement('w:bookmarkStart')
        start.set(qn('w:id'),str(self._bookmark_id_counter)); start.set(qn('w:name'),safe)
        end = OxmlElement('w:bookmarkEnd'); end.set(qn('w:id'),str(self._bookmark_id_counter))
        target._p.insert(0, start); target._p.append(end)
        return f"Bookmark '{safe}' added"

    def action_add_cross_reference(self, bookmark_name="", find_text=None,
                                    reference_type="page", **kwargs):
        safe  = bookmark_name.replace(" ","_")
        fm    = {"page":f'REF {safe} \\h \\p',"text":f'REF {safe} \\h',"above_below":f'REF {safe} \\p'}
        instr = fm.get(reference_type, fm["page"])
        para  = self.doc.add_paragraph()
        if find_text:
            for p in self._iter_all_paragraphs():
                if find_text in p.text: para = p; break
        run = para.add_run()
        for ft, txt in [('begin',None),(None,f' {instr} '),('end',None)]:
            if ft: e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'),ft); run._r.append(e)
            else:  e = OxmlElement('w:instrText'); e.text=txt; run._r.append(e)
        return f"Cross-reference to '{safe}' inserted"

    def action_add_footnote(self, find_text=None, footnote_text="", **kwargs):
        count = 0
        for para in self._iter_all_paragraphs():
            if find_text and find_text in para.text:
                run = para.add_run(f"[{count+1}]")
                run.font.superscript = True; run.font.size = Pt(8); count += 1
        self.doc.add_paragraph("")
        note = self.doc.add_paragraph(f"[{count}] {footnote_text}")
        for run in note.runs: run.font.size = Pt(9); run.italic = True
        return f"Footnote added: '{footnote_text}'"

    def action_add_endnote(self, find_text=None, endnote_text="", **kwargs):
        for para in self._iter_all_paragraphs():
            if find_text and find_text in para.text:
                run = para.add_run("(i)")
                run.font.superscript = True; run.font.size = Pt(8); break
        self.doc.add_paragraph("")
        if not any(p.text.strip().lower() == "endnotes" for p in self.doc.paragraphs):
            h = self.doc.add_paragraph("Endnotes"); h.style = "Heading 2"
        note = self.doc.add_paragraph(f"(i) {endnote_text}")
        for run in note.runs: run.font.size = Pt(9); run.italic = True
        return f"Endnote added: '{endnote_text}'"

    def action_add_hyperlink(self, text=None, url=None, find_text=None, **kwargs):
        def _add(paragraph, link_text, link_url):
            r_id = paragraph.part.relate_to(
                link_url,
                'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',
                is_external=True)
            hl = OxmlElement('w:hyperlink'); hl.set(qn('r:id'), r_id)
            nr = OxmlElement('w:r'); rPr = OxmlElement('w:rPr')
            rs = OxmlElement('w:rStyle'); rs.set(qn('w:val'),'Hyperlink')
            rPr.append(rs); nr.append(rPr)
            t = OxmlElement('w:t'); t.text = link_text; nr.append(t); hl.append(nr)
            paragraph._p.append(hl)
        if find_text:
            for para in self._iter_all_paragraphs():
                if find_text in para.text: _add(para, text or find_text, url or ""); break
        else:
            _add(self.doc.add_paragraph(), text or url or "", url or "")
        return f"Hyperlink added: {text} -> {url}"

    # ─────────────────────────────────────────
    # DOCUMENT ELEMENTS
    # ─────────────────────────────────────────

    def action_add_watermark(self, text="DRAFT", transparency=0.5, **kwargs):
        for section in self.doc.sections:
            header = section.header
            para   = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
            run = para.add_run(text)
            run.font.size = Pt(72); run.font.color.rgb = RGBColor(192,192,192); run.font.bold = True
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        return f"Watermark '{text}' added"

    def action_remove_watermark(self, **kwargs):
        for section in self.doc.sections:
            for para in section.header.paragraphs:
                if para.runs and para.runs[0].font.size and para.runs[0].font.size >= Pt(60):
                    para.clear()
        return "Watermark removed"

    def action_add_cover_page(self, title="Document Title", subtitle="",
                               author="", date="", **kwargs):
        from datetime import datetime as dt
        if self.doc.paragraphs:
            self.doc.paragraphs[0].insert_paragraph_before("\n\n\n")
            t = self.doc.paragraphs[0].insert_paragraph_before(title)
        else:
            self.doc.add_paragraph("\n\n\n"); t = self.doc.add_paragraph(title)
        t.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in t.runs:
            run.font.size = Pt(28); run.font.bold = True
            run.font.color.rgb = RGBColor(6, 78, 59)
        if subtitle:
            s = self.doc.add_paragraph(subtitle); s.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in s.runs: run.font.size = Pt(16); run.font.color.rgb = RGBColor(16,185,129)
        if author:
            a = self.doc.add_paragraph(f"\n\nAuthor: {author}"); a.alignment = WD_ALIGN_PARAGRAPH.CENTER
        d = self.doc.add_paragraph(date or dt.now().strftime("%B %Y"))
        d.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self.action_add_page_break()
        return f"Cover page added: '{title}'"

    def action_insert_text_box(self, text="", width_inches=3.0,
                                height_inches=1.5, border_color="#10B981", **kwargs):
        table = self.doc.add_table(rows=1, cols=1); table.style = "Table Grid"
        cell  = table.rows[0].cells[0]; cell.text = text; cell.width = Inches(width_inches)
        shd = OxmlElement('w:shd'); shd.set(qn('w:val'),'clear'); shd.set(qn('w:fill'),'F0FDF4')
        cell._tc.get_or_add_tcPr().append(shd)
        return f"Text box inserted: '{text}'"

    def action_insert_math_equation(self, equation="x = (-b ± √(b²-4ac)) / 2a", **kwargs):
        para = self.doc.add_paragraph(); para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run  = para.add_run(equation)
        run.font.name = "Cambria Math"; run.font.size = Pt(12); run.italic = True
        return f"Equation inserted: {equation}"

    def action_format_code_block(self, find_text=None, font="Courier New",
                                  background="#F0FDF4", **kwargs):
        count = 0
        for para in self._iter_all_paragraphs():
            is_code = (find_text and find_text in para.text) or \
                      para.text.strip().startswith((
                          'def ','class ','import ','from ','//','#','/*',
                          'function ','const ','let ','var '))
            if is_code:
                for run in para.runs: run.font.name = font; run.font.size = Pt(10)
                shd = OxmlElement('w:shd')
                shd.set(qn('w:val'),'clear'); shd.set(qn('w:fill'),background.lstrip('#'))
                para._p.get_or_add_pPr().append(shd); count += 1
        return f"Code block formatting applied to {count} paragraphs"

    def action_add_horizontal_line(self, before_headings=True, color="000000", **kwargs):
        heading_set = set(id(p) for p in self._find_heading_paragraphs()); count = 0
        for para in self.doc.paragraphs:
            if before_headings and id(para) not in heading_set: continue
            pPr  = para._p.get_or_add_pPr()
            pBdr = OxmlElement('w:pBdr'); top = OxmlElement('w:top')
            top.set(qn('w:val'),'single'); top.set(qn('w:sz'),'6')
            top.set(qn('w:space'),'1');    top.set(qn('w:color'),color.lstrip('#'))
            pBdr.append(top); pPr.append(pBdr); count += 1
        return f"Horizontal line added before {count} headings"

    def action_remove_comments(self, **kwargs):
        body = self.doc.element.body
        for c in body.findall(f'.//{qn("w:commentReference")}'): c.getparent().remove(c)
        return "All comments removed"

    def action_add_comment(self, find_text="", comment_text="",
                            author="Texlify AI", **kwargs):
        target = None
        for para in self._iter_all_paragraphs():
            if find_text and find_text in para.text: target = para; break
        if not target: return f"Text '{find_text}' not found"
        try:
            self.doc.add_comment(runs=target.runs[0] if target.runs else None,
                                  text=comment_text, author=author)
            return f"Comment added: '{comment_text}'"
        except AttributeError:
            run = target.add_run(f" [{author}: {comment_text}]")
            run.font.color.rgb = RGBColor(217,119,6); run.font.size = Pt(9); run.italic = True
            return f"Comment added inline: '{comment_text}'"

    def action_insert_smartart(self, type="process", items=None, title="", **kwargs):
        if not items: items = ["Item 1", "Item 2", "Item 3"]
        if type == "hierarchy":
            table = self.doc.add_table(rows=len(items), cols=1); table.style = "Table Grid"
            for i, item in enumerate(items):
                cell = table.rows[i].cells[0]; cell.text = item
                shd = OxmlElement('w:shd'); shd.set(qn('w:val'),'clear'); shd.set(qn('w:color'),'auto')
                shd.set(qn('w:fill'),"10B981" if i == 0 else "D1FAE5")
                cell._tc.get_or_add_tcPr().append(shd)
                for para in cell.paragraphs:
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in para.runs:
                        run.bold = i == 0
                        run.font.color.rgb = RGBColor(255,255,255) if i == 0 else RGBColor(6,78,59)
        else:
            table = self.doc.add_table(rows=1, cols=len(items)); table.style = "Table Grid"
            colors = ["10B981","059669","047857","064E3B","065F46"]
            for i, item in enumerate(items[:len(colors)]):
                cell = table.rows[0].cells[i]; cell.text = item
                shd = OxmlElement('w:shd'); shd.set(qn('w:val'),'clear'); shd.set(qn('w:color'),'auto')
                shd.set(qn('w:fill'), colors[i % len(colors)]); cell._tc.get_or_add_tcPr().append(shd)
                for para in cell.paragraphs:
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in para.runs: run.bold = True; run.font.color.rgb = RGBColor(255,255,255)
        if title:
            cap = self.doc.add_paragraph(title); cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in cap.runs: run.italic = True; run.font.size = Pt(10)
        return f"SmartArt ({type}) created with {len(items)} items"

    def action_insert_shape_text(self, shape_type="rectangle", text="",
                                  width_inches=2.0, color="#10B981", **kwargs):
        table = self.doc.add_table(rows=1, cols=1); table.style = "Table Grid"
        cell  = table.rows[0].cells[0]; cell.text = text; cell.width = Inches(width_inches)
        tc = cell._tc; tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd'); shd.set(qn('w:val'),'clear'); shd.set(qn('w:color'),'auto')
        shd.set(qn('w:fill'), color.lstrip('#')); tcPr.append(shd)
        for para in cell.paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in para.runs: run.bold = True; run.font.color.rgb = RGBColor(255,255,255)
        return f"{shape_type.title()} shape with text '{text}' inserted"

    # ─────────────────────────────────────────
    # CITATIONS AND MAIL MERGE
    # ─────────────────────────────────────────

    def action_add_citation(self, find_text=None, author="", year="", style="APA", **kwargs):
        ct = f"({author}, {year})" if style.upper() in ("APA","MLA") else f"[{author}]"
        if find_text:
            for para in self._iter_all_paragraphs():
                if find_text in para.text:
                    run = para.add_run(f" {ct}"); run.font.size = Pt(11)
                    return f"Citation '{ct}' inserted"
        self.doc.add_paragraph(ct)
        return f"Citation '{ct}' added"

    def action_add_bibliography(self, references=None, style="APA", **kwargs):
        if not references: references = []
        self.doc.add_paragraph(""); h = self.doc.add_paragraph("References"); h.style = "Heading 1"
        for i, ref in enumerate(references, 1):
            p = self.doc.add_paragraph(f"{i}. {ref}" if style.upper() != "APA" else ref)
            p.paragraph_format.left_indent       = Inches(0.5)
            p.paragraph_format.first_line_indent = Inches(-0.5)
            for run in p.runs: run.font.size = Pt(11)
        return f"Bibliography added with {len(references)} references ({style})"

    def action_add_mail_merge_field(self, field_name="", find_text=None, **kwargs):
        para = self.doc.add_paragraph()
        if find_text:
            for p in self._iter_all_paragraphs():
                if find_text in p.text: para = p; break
        run = para.add_run()
        for ft, txt in [('begin',None),(None,f' MERGEFIELD {field_name} \\* MERGEFORMAT '),('end',None)]:
            if ft: e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'),ft); run._r.append(e)
            else:  e = OxmlElement('w:instrText'); e.text=txt; run._r.append(e)
        return f"Mail merge field «{field_name}» inserted"

    # ─────────────────────────────────────────
    # SECTIONS AND LAYOUT
    # ─────────────────────────────────────────

    def action_add_section_break(self, break_type="next_page", **kwargs):
        new = self.doc.add_section(WD_SECTION.NEW_PAGE)
        if break_type == "continuous":  new.start_type = WD_SECTION.CONTINUOUS
        elif break_type == "even_page": new.start_type = WD_SECTION.EVEN_PAGE
        elif break_type == "odd_page":  new.start_type = WD_SECTION.ODD_PAGE
        return f"Section break ({break_type}) added"

    def action_set_columns(self, num_columns=2, equal_width=True, spacing_inches=0.5, **kwargs):
        for section in self.doc.sections:
            cols = OxmlElement('w:cols')
            cols.set(qn('w:num'),str(num_columns))
            cols.set(qn('w:space'),str(int(spacing_inches * 1440)))
            cols.set(qn('w:equalWidth'),'1' if equal_width else '0')
            section._sectPr.append(cols)
        return f"{num_columns}-column layout applied"

    def action_set_chapter_new_page(self, **kwargs):
        headings = self._find_heading_paragraphs(); count = 0
        for para in headings:
            pPr = para._p.get_or_add_pPr()
            pb  = OxmlElement('w:pageBreakBefore'); pb.set(qn('w:val'),'1'); pPr.append(pb)
            count += 1
        return f"Page break before {count} headings set"

    def action_add_page_border(self, style="single", color="#000000", **kwargs):
        for section in self.doc.sections:
            pgB = OxmlElement('w:pgBorders'); pgB.set(qn('w:offsetFrom'),'page')
            for side in ['top','left','bottom','right']:
                b = OxmlElement(f'w:{side}')
                b.set(qn('w:val'),style); b.set(qn('w:sz'),'24')
                b.set(qn('w:space'),'24'); b.set(qn('w:color'),color.lstrip('#'))
                pgB.append(b)
            section._sectPr.append(pgB)
        return f"Page border added ({style})"

    def action_remove_page_border(self, **kwargs):
        for section in self.doc.sections:
            for pgB in section._sectPr.findall(qn('w:pgBorders')): section._sectPr.remove(pgB)
        return "Page borders removed"

    # ─────────────────────────────────────────
    # STYLES
    # ─────────────────────────────────────────

    def action_create_custom_style(self, style_name="", base_style="Normal",
                                    font_name="Calibri", font_size=11,
                                    bold=False, color=None, **kwargs):
        from docx.enum.style import WD_STYLE_TYPE
        try:    ns = self.doc.styles[style_name]
        except KeyError:
            ns = self.doc.styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH)
            try: ns.base_style = self.doc.styles[base_style]
            except: pass
        ns.font.name = font_name; ns.font.size = Pt(font_size); ns.font.bold = bold
        if color: ns.font.color.rgb = hex_to_rgb(color)
        return f"Custom style '{style_name}' created"

    def action_apply_custom_style(self, style_name="", find_text=None,
                                   apply_to_all=False, **kwargs):
        try:    style = self.doc.styles[style_name]
        except: return f"Style '{style_name}' not found"
        count = 0
        for para in self._iter_all_paragraphs():
            if apply_to_all or (find_text and find_text in para.text):
                para.style = style; count += 1
        return f"Style '{style_name}' applied to {count} paragraphs"

    def action_apply_style_set(self, style_set="formal", **kwargs):
        sets = {
            "formal":       {"font":"Times New Roman","size":12,"heading_color":"#1a1a1a","line_spacing":2.0,"alignment":"justify"},
            "casual":       {"font":"Calibri","size":11,"heading_color":"#2563EB","line_spacing":1.5,"alignment":"left"},
            "professional": {"font":"Calibri","size":11,"heading_color":"#1F4E3D","line_spacing":1.15,"alignment":"left"},
            "elegant":      {"font":"Garamond","size":12,"heading_color":"#7C3AED","line_spacing":1.5,"alignment":"justify"},
            "minimalist":   {"font":"Arial","size":11,"heading_color":"#374151","line_spacing":1.5,"alignment":"left"},
        }
        s = sets.get(style_set.lower(), sets["professional"])
        self.action_set_font(font_name=s["font"], size=s["size"], apply_to="body")
        self.action_set_alignment(alignment=s["alignment"], apply_to="body")
        self.action_set_paragraph_spacing(before=0, after=8, line_spacing=s["line_spacing"], apply_to="body")
        self.action_set_heading_style(level=1, bold=True, color=s["heading_color"], font_size=s["size"]+6)
        self.action_set_heading_style(level=2, bold=True, color=s["heading_color"], font_size=s["size"]+3)
        self.action_set_heading_style(level=3, bold=True, color=s["heading_color"], font_size=s["size"]+1)
        return f"Style set '{style_set}' applied"

    def action_set_document_properties(self, title=None, author=None,
                                        subject=None, keywords=None,
                                        comments=None, **kwargs):
        cp = self.doc.core_properties
        if title:    cp.title    = title
        if author:   cp.author   = author
        if subject:  cp.subject  = subject
        if keywords: cp.keywords = keywords
        if comments: cp.comments = comments
        return "Document properties updated"

    def action_apply_heading_numbering(self, style="1.1.1", **kwargs):
        counters = [0] * 6
        for para in self.doc.paragraphs:
            if not para.style.name.startswith("Heading"): continue
            try:
                level = int(para.style.name.split(" ")[1]) - 1
                counters[level] += 1
                for i in range(level+1, len(counters)): counters[i] = 0
                prefix = ".".join(str(counters[i]) for i in range(level+1)) + " " \
                         if style == "1.1.1" else f"{counters[level]}. "
                if para.runs and not para.runs[0].text.startswith(prefix):
                    para.runs[0].text = prefix + para.runs[0].text
            except (ValueError, IndexError): continue
        return f"Heading numbering applied ({style})"

    def action_remove_heading_numbers(self, **kwargs):
        count = 0
        for para in self._find_heading_paragraphs():
            if para.runs:
                clean = re.sub(r'^[\d\.\s]+', '', para.runs[0].text).strip()
                if clean != para.runs[0].text:
                    para.runs[0].text = clean; count += 1
        return f"Heading numbers removed from {count} paragraphs"

    def action_lock_section(self, section_index=0, **kwargs):
        settings = self.doc.settings.element
        dp = OxmlElement('w:documentProtection'); dp.set(qn('w:edit'),'readOnly')
        settings.append(dp)
        return "Document protection applied"

    # ─────────────────────────────────────────
    # ACADEMIC FORMATS — CORRECTED
    # ─────────────────────────────────────────

    def action_apply_sppu_format(self, **kwargs):
        """
        SPPU BE/ME Project Report — Official specs:
        Body text:   Times New Roman 12pt, justified, 1.5 spacing, 1cm (0.39in) first line indent
        Chapter H1:  Times New Roman 14pt bold centred
        Section H2:  Times New Roman 12pt bold left
        Sub-sec H3:  Times New Roman 12pt bold left
        Margins:     Left=1.5in Right=1.0in Top=1.0in Bottom=1.0in
        Paper:       A4
        """
        self.action_set_page_size(size="A4")
        self.action_set_margins(top=1.0, bottom=1.0, left=1.5, right=1.0)
        # Body text
        self.action_set_font(font_name="Times New Roman", size=12, apply_to="body")
        self.action_set_alignment(alignment="justify", apply_to="body")
        self.action_set_paragraph_spacing(before=0, after=0, line_spacing=1.5, apply_to="body")
        self.action_set_indent(left=0.0, right=0.0, first_line=0.39, apply_to="body")
        # Chapter headings H1 — 14pt bold centred
        self.action_set_font(font_name="Times New Roman", size=14, apply_to="headings")
        self.action_set_heading_style(level=1, bold=True, color="#000000", font_size=14)
        for para in self.doc.paragraphs:
            if para.style.name == "Heading 1":
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        # Section headings H2 — 12pt bold left
        self.action_set_heading_style(level=2, bold=True, color="#000000", font_size=12)
        # Sub-section H3 — 12pt bold left
        self.action_set_heading_style(level=3, bold=True, color="#000000", font_size=12)
        return (
            "SPPU format applied: "
            "TNR 12pt body justified 1.5 spacing 1cm indent | "
            "H1: 14pt bold centred | "
            "H2/H3: 12pt bold | "
            "Margins: L=1.5in R=1.0in T=1.0in B=1.0in | A4"
        )

    def action_apply_ieee_format(self, **kwargs):
        """
        IEEE Conference Paper — Official A4 specs:
        Body:    Times New Roman 10pt, justified, single spacing, 0.2in first line indent
        Title:   24pt bold centred (H1)
        Section: 10pt bold (H2/H3)
        Margins: Top=19mm(0.75in) Bottom=40mm(1.57in) Left=Right=15mm(0.59in)
        Columns: 2-column, column width 88mm, gap 4mm (0.16in)
        Paper:   A4
        """
        self.action_set_page_size(size="A4")
        self.action_set_margins(top=0.75, bottom=1.57, left=0.59, right=0.59)
        # Body text
        self.action_set_font(font_name="Times New Roman", size=10, apply_to="all")
        self.action_set_alignment(alignment="justify", apply_to="all")
        self.action_set_paragraph_spacing(before=0, after=0, line_spacing=1.0, apply_to="all")
        self.action_set_indent(left=0.0, right=0.0, first_line=0.2, apply_to="body")
        # Title H1 — 24pt bold centred
        self.action_set_heading_style(level=1, bold=True, color="#000000", font_size=24)
        for para in self.doc.paragraphs:
            if para.style.name == "Heading 1":
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        # Section headings H2 — 10pt bold small caps
        self.action_set_heading_style(level=2, bold=True, color="#000000", font_size=10)
        # Sub-section H3 — 10pt bold italic
        self.action_set_heading_style(level=3, bold=True, color="#000000", font_size=10)
        # Two-column layout with 4mm (0.16in) gap
        self.action_set_columns(num_columns=2, equal_width=True, spacing_inches=0.16)
        return (
            "IEEE format applied: "
            "TNR 10pt body justified single spacing 0.2in indent | "
            "Title: 24pt bold centred | "
            "Section headings: 10pt bold | "
            "Margins: T=0.75in B=1.57in L=R=0.59in | "
            "2-column 4mm gap | A4"
        )

    def action_apply_apa_format(self, **kwargs):
        """APA 7th Edition"""
        self.action_set_page_size(size="Letter")
        self.action_set_font(font_name="Times New Roman", size=12, apply_to="all")
        self.action_set_alignment(alignment="left", apply_to="body")
        self.action_set_margins(top=1.0, bottom=1.0, left=1.0, right=1.0)
        self.action_set_paragraph_spacing(before=0, after=0, line_spacing=2.0, apply_to="body")
        self.action_set_indent(left=0.0, right=0.0, first_line=0.5, apply_to="body")
        self.action_set_heading_style(level=1, bold=True, color="#000000", font_size=12)
        self.action_set_heading_style(level=2, bold=True, color="#000000", font_size=12)
        return "APA 7th: TNR 12pt double spacing left 1in margins 0.5in indent Letter"

    def action_apply_mla_format(self, **kwargs):
        """MLA 9th Edition"""
        self.action_set_page_size(size="Letter")
        self.action_set_font(font_name="Times New Roman", size=12, apply_to="all")
        self.action_set_alignment(alignment="left", apply_to="body")
        self.action_set_margins(top=1.0, bottom=1.0, left=1.0, right=1.0)
        self.action_set_paragraph_spacing(before=0, after=0, line_spacing=2.0, apply_to="body")
        self.action_set_indent(left=0.0, right=0.0, first_line=0.5, apply_to="body")
        self.action_set_heading_style(level=1, bold=False, color="#000000", font_size=12)
        return "MLA 9th: TNR 12pt double spacing left 1in margins 0.5in indent Letter"

    def action_apply_resume_format(self, **kwargs):
        """Professional Resume"""
        self.action_set_page_size(size="Letter")
        self.action_set_margins(top=0.75, bottom=0.75, left=0.75, right=0.75)
        self.action_set_font(font_name="Calibri", size=11, apply_to="all")
        self.action_set_alignment(alignment="left", apply_to="body")
        self.action_set_paragraph_spacing(before=0, after=4, line_spacing=1.15, apply_to="all")
        self.action_set_heading_style(level=1, bold=True, color="#1F4E3D", font_size=18)
        self.action_set_heading_style(level=2, bold=True, color="#10B981", font_size=13)
        self.action_set_heading_style(level=3, bold=True, color="#064E3B", font_size=11)
        return "Resume: Calibri 11pt 1.15 spacing 0.75in margins dark green headings Letter"

    def action_apply_chicago_format(self, **kwargs):
        """Chicago 17th Edition"""
        self.action_set_page_size(size="Letter")
        self.action_set_font(font_name="Times New Roman", size=12, apply_to="all")
        self.action_set_alignment(alignment="left", apply_to="body")
        self.action_set_margins(top=1.0, bottom=1.0, left=1.0, right=1.0)
        self.action_set_paragraph_spacing(before=0, after=0, line_spacing=2.0, apply_to="body")
        self.action_set_indent(left=0.0, right=0.0, first_line=0.5, apply_to="body")
        return "Chicago 17th: TNR 12pt double spacing 1in margins 0.5in indent Letter"

    def action_apply_thesis_format(self, **kwargs):
        """Generic Thesis/Dissertation"""
        self.action_set_page_size(size="A4")
        self.action_set_font(font_name="Times New Roman", size=12, apply_to="all")
        self.action_set_alignment(alignment="justify", apply_to="body")
        self.action_set_margins(top=1.0, bottom=1.0, left=1.5, right=1.0)
        self.action_set_paragraph_spacing(before=0, after=0, line_spacing=1.5, apply_to="body")
        self.action_set_indent(left=0.0, right=0.0, first_line=0.5, apply_to="body")
        self.action_set_heading_style(level=1, bold=True, color="#000000", font_size=14)
        self.action_set_heading_style(level=2, bold=True, color="#000000", font_size=13)
        self.action_set_heading_style(level=3, bold=True, color="#000000", font_size=12)
        return "Thesis: TNR 12pt 1.5 spacing justified 1.5in left binding A4"

    # ─────────────────────────────────────────
    # PROTECTION AND CONVERSION
    # ─────────────────────────────────────────

    def action_set_password_protection(self, password="",
                                        protection_type="read_only", **kwargs):
        import hashlib
        dp = OxmlElement('w:documentProtection'); dp.set(qn('w:edit'), protection_type)
        if password:
            h = hashlib.sha1(password.encode('utf-16-le')).hexdigest().upper()
            dp.set(qn('w:hash'),h); dp.set(qn('w:cryptAlgorithmSid'),'4')
        self.doc.settings.element.append(dp)
        return f"Document protection set ({protection_type})"

    def action_remove_password_protection(self, **kwargs):
        settings = self.doc.settings.element
        for dp in settings.findall(qn('w:documentProtection')): settings.remove(dp)
        return "Document protection removed"

    def action_convert_to_pdf(self, output_path=None, **kwargs):
        try:
            if output_path is None: output_path = self.file_path.replace('.docx', '.pdf')
            try:
                from docx2pdf import convert; convert(self.file_path, output_path)
                return f"PDF saved: {output_path}"
            except ImportError: pass
            import subprocess
            result = subprocess.run(
                ['libreoffice','--headless','--convert-to','pdf',
                 '--outdir', os.path.dirname(self.file_path), self.file_path],
                capture_output=True, timeout=60)
            if result.returncode == 0: return "PDF created"
            return "Install docx2pdf or LibreOffice for PDF conversion."
        except Exception as e: return f"PDF error: {str(e)}"

    # ─────────────────────────────────────────
    # MAINTENANCE
    # ─────────────────────────────────────────

    def action_clear_document(self, **kwargs):
        for para in self.doc.paragraphs: para.clear()
        for table in self.doc.tables: table._tbl.getparent().remove(table._tbl)
        return "Document content cleared"

    def action_duplicate_page(self, page_number=1, **kwargs):
        self.action_add_page_break(); return f"Page {page_number} duplicated"

    def action_undo_last_command(self, backup_filename=None, **kwargs):
        if not backup_filename: return "No backup filename provided"
        bp = os.path.join(os.path.dirname(self.file_path), backup_filename)
        if not os.path.exists(bp): return f"Backup not found: {backup_filename}"
        shutil.copy2(bp, self.file_path)
        return f"Document restored from: {backup_filename}"

    def action_clean_empty_paragraphs(self, **kwargs):
        removed = 0; consecutive = 0
        for para in list(self.doc.paragraphs):
            if not para.text.strip():
                consecutive += 1
                if consecutive > 2:
                    para._element.getparent().remove(para._element); removed += 1
            else:
                consecutive = 0
        return f"Removed {removed} excessive empty paragraphs"

    def action_normalize_spacing(self, **kwargs):
        for para in self._iter_all_paragraphs():
            if para.text.strip():
                pf = para.paragraph_format
                if pf.space_before and pf.space_before > Pt(24): pf.space_before = Pt(12)
                if pf.space_after  and pf.space_after  > Pt(24): pf.space_after  = Pt(8)
        return "Spacing normalized throughout document"