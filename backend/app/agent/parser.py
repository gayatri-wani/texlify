import json
from groq import Groq
from app.core.config import settings

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

COMPLETE LIST OF AVAILABLE ACTIONS:

BASIC FORMATTING:
- set_font: { "font_name": str, "size": int, "bold": bool, "italic": bool, "color": "#RRGGBB", "apply_to": "all|headings|body", "find_text": str }
- replace_font: { "old_font": str, "new_font": str }
- set_heading_style: { "level": 1-6, "bold": bool, "color": "#RRGGBB", "font_size": int, "underline": bool }
- apply_heading_styles: {}
- set_paragraph_spacing: { "before": int, "after": int, "line_spacing": float, "apply_to": "all|headings|body" }
- set_line_spacing_exact: { "value_pt": float, "apply_to": "all|body|headings" }
- set_alignment: { "alignment": "left|center|right|justify", "apply_to": "all|headings|body", "find_text": str }
- set_margins: { "top": float, "bottom": float, "left": float, "right": float }

ADVANCED TEXT FORMATTING:
- set_underline: { "apply_to": "all|headings|body", "find_text": str }
- set_strikethrough: { "apply_to": "all|headings|body", "find_text": str }
- set_highlight: { "color": "yellow|green|cyan|pink|blue|red|orange|turquoise|gray", "find_text": str, "apply_to": "all|headings|body", "selected_texts": [str] }
- search_and_highlight: { "find_text": str, "color": "yellow|green|cyan|pink|blue|red" }
- remove_highlight: { "apply_to": "all", "find_text": str }
- set_superscript: { "find_text": str }
- set_subscript: { "find_text": str }
- set_text_color: { "color": "#RRGGBB", "apply_to": "all|headings|body", "find_text": str, "selected_texts": [str] }
- set_indent: { "left": float, "right": float, "first_line": float, "apply_to": "all|body|headings" }
- remove_formatting: { "apply_to": "all|headings|body", "find_text": str }
- set_character_spacing: { "spacing": float }
- set_text_case: { "case": "upper|lower|title|sentence", "apply_to": "all|headings|body" }
- copy_formatting: { "source_text": str, "target_text": str }
- set_paragraph_shading: { "color": "#RRGGBB", "apply_to": "all|body|headings", "find_text": str }
- set_paragraph_border: { "style": "single|double|thick", "color": "#RRGGBB", "sides": "all|top|bottom", "find_text": str }
- set_keep_with_next: { "apply_to": "headings|all" }
- set_widow_orphan_control: { "enabled": bool }
- set_drop_cap: { "paragraph_index": int, "lines": int, "font_name": str }
- set_text_effect: { "find_text": str, "effect": "shadow|outline|emboss|engrave|small_caps|all_caps" }
- remove_text_effects: { "find_text": str }

TRACK CHANGES:
- enable_track_changes: {}
- disable_track_changes: {}
- accept_all_changes: {}
- reject_all_changes: {}

CHECKLISTS:
- add_checklist: { "items": [{"text": str, "checked": bool}] }
- convert_to_checklist: {}

SELECTION-BASED:
- apply_to_selection: {
    "selected_texts": [str],
    "command_type": "bold|italic|underline|strikethrough|heading|font|color|highlight|remove_highlight|align|uppercase|lowercase|capitalize|remove_formatting|remove_bold|remove_italic",
    "font_name": str, "font_size": int, "color": "#RRGGBB",
    "highlight_color": "yellow|green|cyan|pink|blue|red",
    "alignment": "left|center|right|justify",
    "make_heading": 1-6
  }

TEXT OPERATIONS:
- find_replace: { "find": str, "replace": str, "case_sensitive": bool }
- add_text: { "text": str, "position": "beginning|end", "new_paragraph": bool }
- delete_text: { "find": str }
- count_words: {}
- count_paragraphs: {}
- extract_text: {}
- set_language: { "language": "en-US|en-GB|hi-IN|fr-FR" }

LISTS AND NUMBERING:
- add_bullet_list: { "items": ["item1", "item2"] }
- add_numbered_list: { "items": ["item1", "item2"] }
- add_multilevel_list: { "items": [{"text": str, "level": 0|1|2}] }
- add_checklist: { "items": [{"text": str, "checked": bool}] }
- convert_to_bullets: {}
- convert_to_checklist: {}
- restart_numbering: { "list_style": str }

PAGE MANAGEMENT:
- add_page_break: {}
- add_blank_page: {}
- set_page_size: { "size": "A4|Letter|A3|A5|Legal" }
- set_page_orientation: { "orientation": "portrait|landscape" }
- set_page_color: { "color": "#RRGGBB" }
- add_line_numbers: { "start": int, "step": int, "restart": "newPage|newSection|continuous" }
- remove_line_numbers: {}
- set_page_number_start: { "start": int }

HEADERS AND FOOTERS:
- add_header: { "text": str, "alignment": "left|center|right" }
- add_footer: { "text": str, "alignment": "left|center|right" }
- remove_header: {}
- remove_footer: {}
- add_page_numbers: { "position": "header|footer", "alignment": "left|center|right", "format": "Page X|X of Y|X" }
- set_different_first_page_header: { "first_header": str, "rest_header": str }
- set_section_header: { "section_index": int, "text": str, "alignment": str }
- set_section_footer: { "section_index": int, "text": str, "alignment": str }
- insert_date_field: {}
- insert_page_count_field: { "position": "footer|header" }
- set_page_number_start: { "start": int }

IMAGES AND MEDIA:
- insert_image: { "image_path": str, "width_inches": float, "height_inches": float, "alignment": str, "caption": str }
- insert_image_with_border: { "image_path": str, "width_inches": float, "border_color": "#RRGGBB", "border_size": int, "caption": str }
- insert_logo: { "image_path": str, "page": "first|all", "position": "top_right|top_left|top_center", "width_inches": float }
- caption_image: { "image_index": int, "caption_text": str, "label": "Figure" }

VISUAL ELEMENTS AND SHAPES:
- insert_styled_box: { "text": str, "style": "shadow|border|glow|gradient|rounded|info|warning|success|danger|callout", "color": "#RRGGBB", "width_inches": float }
- insert_highlight_box: { "text": str, "box_type": "note|tip|warning|important|caution" }
- insert_divider: { "style": "thick|double|dotted|dashed|wave|triple", "color": "#RRGGBB", "text": str }
- insert_badge: { "text": str, "color": "#RRGGBB", "text_color": "#RRGGBB" }
- insert_smartart: { "type": "process|hierarchy|list|cycle|relationship", "items": [str], "title": str }
- insert_shape_text: { "shape_type": "rectangle|rounded|circle|banner", "text": str, "width_inches": float, "color": "#RRGGBB" }

TABLES:
- insert_table: { "rows": int, "cols": int, "headers": ["col1", "col2"] }
- format_table: { "style": str }
- set_table_cell_color: { "table_index": int, "row": int, "col": int, "color": "#RRGGBB" }
- set_table_header_color: { "table_index": int, "color": "#RRGGBB" }
- set_table_borders: { "table_index": int, "border_color": "#RRGGBB", "border_size": int }
- merge_table_cells: { "table_index": int, "start_row": int, "start_col": int, "end_row": int, "end_col": int }
- set_column_width: { "table_index": int, "col": int, "width_inches": float }
- add_table_row: { "table_index": int, "data": ["cell1", "cell2"] }
- delete_table_row: { "table_index": int, "row_index": int }
- caption_table: { "table_index": int, "caption_text": str, "label": "Table" }
- sort_table: { "table_index": int, "col": int, "ascending": bool }
- set_table_cell_alignment: { "table_index": int, "row": int, "col": int, "alignment": str }
- set_table_row_height: { "table_index": int, "row_index": int, "height_inches": float }

REFERENCES AND NAVIGATION:
- add_table_of_contents: { "title": str, "max_level": int, "clickable": true }
- add_table_of_figures: { "title": str, "label": "Figure|Table" }
- add_index: { "entries": ["term1", "term2"], "title": str }
- add_bookmark: { "name": str, "find_text": str }
- add_cross_reference: { "bookmark_name": str, "find_text": str, "reference_type": "page|text|above_below" }
- add_internal_link: { "link_text": str, "target_heading": str, "find_in_para": str }
- link_all_headings: {}
- add_footnote: { "find_text": str, "footnote_text": str }
- add_endnote: { "find_text": str, "endnote_text": str }
- add_hyperlink: { "text": str, "url": str, "find_text": str }

DOCUMENT ELEMENTS:
- add_watermark: { "text": str }
- remove_watermark: {}
- add_cover_page: { "title": str, "subtitle": str, "author": str, "date": str }
- insert_text_box: { "text": str, "width_inches": float }
- insert_math_equation: { "equation": str }
- format_code_block: { "find_text": str, "font": str }
- remove_comments: {}
- add_comment: { "find_text": str, "comment_text": str, "author": str }
- add_horizontal_line: { "before_headings": bool, "color": "#RRGGBB" }
- insert_highlight_box: { "text": str, "box_type": "note|tip|warning|important|caution" }
- insert_divider: { "style": "thick|double|dotted|dashed|wave", "color": "#RRGGBB" }

CITATIONS AND MAIL MERGE:
- add_citation: { "find_text": str, "author": str, "year": str, "style": "APA|MLA|IEEE" }
- add_bibliography: { "references": ["ref1", "ref2"], "style": "APA|IEEE|MLA" }
- add_mail_merge_field: { "field_name": str, "find_text": str }

SECTIONS AND LAYOUT:
- add_section_break: { "break_type": "next_page|continuous|even_page|odd_page" }
- set_columns: { "num_columns": int, "spacing_inches": float }
- set_chapter_new_page: {}
- add_page_border: { "style": "single|double|thick", "color": "#RRGGBB" }
- remove_page_border: {}

CUSTOM STYLES:
- create_custom_style: { "style_name": str, "base_style": str, "font_name": str, "font_size": int, "bold": bool, "color": "#RRGGBB" }
- apply_custom_style: { "style_name": str, "find_text": str, "apply_to_all": bool }
- apply_style_set: { "style_set": "formal|casual|professional|elegant|minimalist" }
- set_document_properties: { "title": str, "author": str, "subject": str, "keywords": str }
- apply_heading_numbering: { "style": "1.1.1|I.A.1" }
- remove_heading_numbers: {}
- apply_heading_styles: {}

ACADEMIC AND PROFESSIONAL FORMATS:
- apply_sppu_format: {}
- apply_apa_format: {}
- apply_ieee_format: {}
- apply_mla_format: {}
- apply_resume_format: {}
- apply_chicago_format: {}
- apply_thesis_format: {}

PROTECTION AND CONVERSION:
- set_password_protection: { "password": str, "protection_type": "read_only|forms|comments" }
- remove_password_protection: {}
- convert_to_pdf: {}

MAINTENANCE:
- clear_document: {}
- duplicate_page: { "page_number": int }
- clean_empty_paragraphs: {}
- normalize_spacing: {}
- replace_font: { "old_font": str, "new_font": str }
- extract_text: {}
- count_words: {}
- count_paragraphs: {}

IMPORTANT RULES:
1. Respond ONLY with valid JSON — no markdown, no extra text outside JSON
2. Use multiple actions when a command needs several steps
3. Always use hex codes for colors
4. SPPU: TNR 12pt, 15pt H1 centred, 1.5 spacing, justified, L=1.5in R=1.0in T=B=1.0in, A4, 1cm indent
5. IEEE: TNR 10pt, 2-col, justified, T=0.75in B=1.69in L=R=0.56in, single spacing, A4
6. APA: TNR 12pt, double spacing, left, 1in margins, 0.5in indent, Letter
7. MLA: TNR 12pt, double spacing, left, 1in margins, 0.5in indent, Letter
8. Resume: Calibri 11pt, 1.15 spacing, 0.75in margins, dark green headings, Letter
9. Chicago: TNR 12pt, double spacing, 1in margins, 0.5in indent, Letter
10. Thesis: TNR 12pt, 1.5 spacing, justified, 1.5in left (binding), A4
11. For clickable TOC use add_table_of_contents with clickable=true — it auto-adds bookmarks to all headings
12. For internal links use add_internal_link with link_text and target_heading
13. For "set up proper heading styles like Word" use apply_heading_styles
14. For shadow/glow/outline text effects use set_text_effect
15. For colored boxes/callouts use insert_styled_box or insert_highlight_box
16. For decorative dividers use insert_divider
17. For badges/labels use insert_badge
18. For bordered images use insert_image_with_border
19. For highlight use set_highlight — uses dual method (w:highlight + w:shd) for reliability
20. Never add comments inside JSON
21. Do not wrap response in markdown code fences
"""


def parse_command(command: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Command: {command}"}
            ],
            temperature=0.1,
            max_tokens=2000,
        )
        content = response.choices[0].message.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content.strip())
    except json.JSONDecodeError:
        return {
            "actions": [],
            "summary": "Could not parse command. Please try rephrasing.",
            "error": True
        }
    except Exception as e:
        return {
            "actions": [],
            "summary": f"Agent error: {str(e)}",
            "error": True
        }