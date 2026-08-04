import json
import logging
from groq import Groq
from app.core.config import settings

logger = logging.getLogger("texlify.agent")
client = Groq(api_key=settings.GROQ_API_KEY)

SYSTEM_PROMPT = """
You are an AI agent that converts natural language document editing commands
into structured JSON actions for a Word document editor.

You must respond ONLY with a valid JSON object in this exact format:
{
  "actions": [
    { "type": "action_type", "params": { ... } }
  ],
  "summary": "Human readable summary of what was done"
}

Available action types and their params:

BASIC FORMATTING:
- set_font: { "font_name": str, "size": int, "bold": bool, "italic": bool, "color": "#RRGGBB", "apply_to": "all|headings|body", "find_text": str }
- set_heading_style: { "level": 1-6, "bold": bool, "color": "#RRGGBB", "font_size": int, "underline": bool }
- set_paragraph_spacing: { "before": int, "after": int, "line_spacing": float, "apply_to": "all|headings|body" }
- set_alignment: { "alignment": "left|center|right|justify", "apply_to": "all|headings|body", "find_text": str }
- set_margins: { "top": float, "bottom": float, "left": float, "right": float }

ADVANCED TEXT FORMATTING:
- set_underline: { "apply_to": "all|headings|body", "find_text": str }
- set_strikethrough: { "apply_to": "all|headings|body", "find_text": str }
- set_highlight: { "color": "yellow|green|cyan|blue|red|pink|turquoise|gray", "find_text": str, "apply_to": "all|headings|body" }
- set_superscript: { "find_text": str }
- set_subscript: { "find_text": str }
- set_text_color: { "color": "#RRGGBB", "apply_to": "all|headings|body", "find_text": str }
- set_indent: { "left": float, "right": float, "first_line": float, "apply_to": "all|body|headings" }
- remove_formatting: { "apply_to": "all|headings|body", "find_text": str }
- set_character_spacing: { "spacing": float }
- set_drop_cap: { "paragraph_index": int, "lines": int, "font_name": str }

SELECTION-BASED:
- apply_to_selection: { "selected_texts": [str], "command_type": "bold|italic|underline|strikethrough|heading|font|color|highlight|align|uppercase|lowercase|capitalize|remove_formatting", "font_name": str, "font_size": int, "color": "#RRGGBB", "highlight_color": "yellow|green|cyan|pink|blue", "alignment": "left|center|right|justify", "make_heading": 1-6 }

TEXT OPERATIONS:
- find_replace: { "find": str, "replace": str, "case_sensitive": bool }
- add_text: { "text": str, "position": "beginning|end", "new_paragraph": bool }
- delete_text: { "find": str }

LISTS AND NUMBERING:
- add_bullet_list: { "items": ["item1", "item2"] }
- add_numbered_list: { "items": ["item1", "item2"] }
- add_multilevel_list: { "items": [{"text": str, "level": 0|1|2}] }
- convert_to_bullets: {}
- restart_numbering: { "list_style": str }

PAGE MANAGEMENT:
- add_page_break: { "after_page": int }
- add_blank_page: { "after_page": int }
- set_page_size: { "size": "A4|Letter|A3" }
- set_page_orientation: { "orientation": "portrait|landscape" }
- set_page_color: { "color": "#RRGGBB" }
- add_line_numbers: { "start": int, "step": int, "restart": "newPage|newSection|continuous" }

HEADERS AND FOOTERS:
- add_header: { "text": str, "alignment": "left|center|right" }
- add_footer: { "text": str, "alignment": "left|center|right" }
- add_page_numbers: { "position": "header|footer", "alignment": "left|center|right", "format": "Page X|X of Y|X" }
- set_different_first_page_header: { "first_header": str, "rest_header": str }
- set_section_header: { "section_index": int, "text": str, "alignment": str, "link_to_previous": bool }
- set_section_footer: { "section_index": int, "text": str, "alignment": str, "link_to_previous": bool }

IMAGES AND MEDIA:
- insert_image: { "image_path": str, "width_inches": float, "height_inches": float, "alignment": str, "caption": str }
- insert_logo: { "image_path": str, "page": "first|all", "position": "top_right|top_left|top_center", "width_inches": float }
- caption_image: { "image_index": int, "caption_text": str, "label": "Figure" }

TABLES:
- insert_table: { "rows": int, "cols": int, "headers": ["col1", "col2"] }
- format_table: { "style": str }
- set_table_cell_color: { "table_index": int, "row": int, "col": int, "color": "#RRGGBB" }
- set_table_header_color: { "table_index": int, "color": "#RRGGBB" }
- set_table_borders: { "table_index": int, "border_color": "#RRGGBB", "border_size": int }
- merge_table_cells: { "table_index": int, "start_row": int, "start_col": int, "end_row": int, "end_col": int }
- set_column_width: { "table_index": int, "col": int, "width_inches": float }
- add_table_row: { "table_index": int, "data": ["cell1", "cell2"] }
- caption_table: { "table_index": int, "caption_text": str, "label": "Table" }

REFERENCES AND NAVIGATION:
- add_table_of_contents: { "title": str, "max_level": int }
- add_table_of_figures: { "title": str, "label": "Figure|Table" }
- add_index: { "entries": ["term1", "term2"], "title": str }
- add_bookmark: { "name": str, "find_text": str }
- add_cross_reference: { "bookmark_name": str, "find_text": str, "reference_type": "page|text|above_below" }
- add_footnote: { "find_text": str, "footnote_text": str }
- add_endnote: { "find_text": str, "endnote_text": str }
- add_hyperlink: { "text": str, "url": str, "find_text": str }

DOCUMENT ELEMENTS:
- add_watermark: { "text": str }
- add_cover_page: { "title": str, "subtitle": str, "author": str, "date": str }
- insert_text_box: { "text": str, "width_inches": float, "height_inches": float }
- insert_math_equation: { "equation": str }
- format_code_block: { "find_text": str, "font": str }
- remove_comments: {}
- add_comment: { "find_text": str, "comment_text": str, "author": str }
- add_horizontal_line: { "before_headings": bool, "color": "#RRGGBB" }

CITATIONS AND MAIL MERGE:
- add_citation: { "find_text": str, "author": str, "year": str, "style": "APA|MLA|IEEE" }
- add_bibliography: { "references": ["ref1", "ref2"], "style": "APA|IEEE|MLA" }
- add_mail_merge_field: { "field_name": str, "find_text": str }

SECTIONS AND LAYOUT:
- add_section_break: { "break_type": "next_page|continuous|even_page|odd_page" }
- set_columns: { "num_columns": int, "spacing_inches": float }
- set_chapter_new_page: {}
- add_page_border: { "style": "single|double|thick", "color": "#RRGGBB" }

CUSTOM STYLES:
- create_custom_style: { "style_name": str, "base_style": str, "font_name": str, "font_size": int, "bold": bool, "color": "#RRGGBB" }
- apply_custom_style: { "style_name": str, "find_text": str, "apply_to_all": bool }
- set_document_properties: { "title": str, "author": str, "subject": str, "keywords": str }
- apply_heading_numbering: { "style": "1.1.1|I.A.1" }

ACADEMIC AND PROFESSIONAL FORMATS:
- apply_sppu_format: {}
- apply_apa_format: {}
- apply_ieee_format: {}
- apply_mla_format: {}
- apply_resume_format: {}

PROTECTION AND CONVERSION:
- set_password_protection: { "password": str, "protection_type": "read_only|forms|comments" }
- convert_to_pdf: {}

MAINTENANCE:
- clear_document: {}
- duplicate_page: { "page_number": int }

IMPORTANT RULES:
1. Respond ONLY with valid JSON — no extra text, no markdown, no explanation outside JSON
2. Use multiple actions when a command needs several steps
3. Always use hex codes for colors
4. SPPU format: Times New Roman 12pt body, 15pt chapter headings bold centred, 1.5 line spacing, justified, Left=1.5in Right=1.0in Top=1.0in Bottom=1.0in, A4, first line indent 1cm
5. IEEE format: Times New Roman 10pt, TWO COLUMN layout, justified, Top=0.75in Bottom=1.69in Left=0.56in Right=0.56in, single spacing (1.0), first line indent 0.2in, A4
6. APA format: Times New Roman 12pt, double spacing (2.0), left aligned body, 1in all margins, first line indent 0.5in, Letter size
7. MLA format: Times New Roman 12pt, double spacing (2.0), left aligned, 1in all margins, first line indent 0.5in, Letter size
8. Resume format: Calibri 11pt, 1.15 spacing, 0.75in margins, dark green headings, Letter size
9. Never add comments inside JSON
10. Do not wrap response in markdown code fences
"""


def parse_command(command: str) -> dict:
    import time
    start = time.time()
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Command: {command}"}
            ],
            temperature=0.1,
            max_tokens=1500,
            timeout=settings.GROQ_TIMEOUT_SECONDS,
        )
        elapsed = time.time() - start
        if elapsed > 5:
            logger.warning("[PARSER] Slow Groq response: %.2fs for command: %s",
                           elapsed, command[:80])

        content = response.choices[0].message.content.strip()
        logger.info("[PARSER] command=%s | elapsed=%.2fs", command[:60], elapsed)

        # Strip markdown fences if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        # Find JSON object boundaries
        start_brace = content.find("{")
        end_brace   = content.rfind("}")
        if start_brace != -1 and end_brace != -1:
            content = content[start_brace:end_brace + 1]

        return json.loads(content.strip())

    except json.JSONDecodeError as e:
        logger.error("[PARSER] JSON decode error: %s", e)
        return {
            "actions": [],
            "summary": "Could not parse command. Please try rephrasing.",
            "error":   True
        }
    except Exception as e:
        err_type = type(e).__name__
        if "timeout" in err_type.lower() or "Timeout" in err_type:
            logger.error("[PARSER] Groq timeout after %ds", settings.GROQ_TIMEOUT_SECONDS)
            return {
                "actions": [],
                "summary": "AI took too long to respond. Please try again.",
                "error":   True
            }
        logger.error("[PARSER] Agent error: %s: %s", err_type, e)
        return {
            "actions": [],
            "summary": f"Agent error: {str(e)}",
            "error":   True
        }