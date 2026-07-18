import json
import traceback
from groq import Groq
from app.core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

SYSTEM_PROMPT = """You convert document editing commands to JSON.

Respond ONLY with this JSON format, nothing else:
{"actions": [{"type": "action_name", "params": {}}], "summary": "what was done"}

AVAILABLE ACTIONS:

FORMATTING:
set_font(font_name, size, bold, italic, color, apply_to="all|headings|body", find_text)
set_heading_style(level, bold, color, font_size, underline)
apply_heading_styles()
set_alignment(alignment="left|center|right|justify", apply_to, find_text)
set_margins(top, bottom, left, right)
set_paragraph_spacing(before, after, line_spacing, apply_to)
set_line_spacing_exact(value_pt, apply_to)
set_underline(apply_to, find_text)
set_strikethrough(apply_to, find_text)
set_highlight(color="yellow|green|cyan|pink|blue|red|orange|gray", find_text, apply_to, selected_texts=[])
search_and_highlight(find_text, color)
remove_highlight(apply_to, find_text)
set_superscript(find_text)
set_subscript(find_text)
set_text_color(color, apply_to, find_text)
set_indent(left, right, first_line, apply_to)
remove_formatting(apply_to, find_text)
set_character_spacing(spacing)
set_text_case(case="upper|lower|title|sentence", apply_to)
copy_formatting(source_text, target_text)
set_paragraph_shading(color, apply_to, find_text)
set_paragraph_border(style="single|double", color, sides="all|top|bottom", find_text)
set_keep_with_next(apply_to)
set_widow_orphan_control(enabled)
set_drop_cap(paragraph_index, lines, font_name)
set_text_effect(find_text, effect="shadow|outline|emboss|engrave|small_caps|all_caps")
remove_text_effects(find_text)
replace_font(old_font, new_font)

TRACK CHANGES:
enable_track_changes()
disable_track_changes()
accept_all_changes()
reject_all_changes()

SELECTION:
apply_to_selection(selected_texts=[], command_type="bold|italic|underline|strikethrough|heading|font|color|highlight|remove_highlight|align|uppercase|lowercase|capitalize|remove_formatting|remove_bold|remove_italic", font_name, font_size, color, highlight_color, alignment, make_heading)

TEXT:
find_replace(find, replace, case_sensitive)
add_text(text, position="end|beginning", new_paragraph)
delete_text(find)
count_words()
count_paragraphs()
set_language(language="en-US|en-GB|hi-IN")

LISTS:
add_bullet_list(items=[])
add_numbered_list(items=[])
add_multilevel_list(items=[{"text":"","level":0}])
add_checklist(items=[{"text":"","checked":false}])
convert_to_bullets()
convert_to_checklist()
restart_numbering(list_style)

PAGE:
add_page_break()
add_blank_page()
set_page_size(size="A4|Letter|A3|A5|Legal")
set_page_orientation(orientation="portrait|landscape")
set_page_color(color)
add_line_numbers(start, step, restart)
remove_line_numbers()
set_page_number_start(start)

HEADERS/FOOTERS:
add_header(text, alignment)
add_footer(text, alignment)
remove_header()
remove_footer()
add_page_numbers(position="header|footer", alignment, format="Page X|X of Y|X")
set_different_first_page_header(first_header, rest_header)
set_section_header(section_index, text, alignment)
set_section_footer(section_index, text, alignment)
insert_date_field()
insert_page_count_field(position)

IMAGES:
insert_image(image_path, width_inches, height_inches, alignment, caption)
insert_image_with_border(image_path, width_inches, border_color, border_size, caption)
insert_logo(image_path, page, position, width_inches)
caption_image(image_index, caption_text, label)

VISUAL ELEMENTS:
insert_styled_box(text, style="shadow|border|glow|info|warning|success|danger|callout", color, width_inches)
insert_highlight_box(text, box_type="note|tip|warning|important|caution")
insert_divider(style="thick|double|dotted|dashed|wave", color, text)
insert_badge(text, color, text_color)
insert_smartart(type="process|hierarchy|list", items=[], title)
insert_shape_text(shape_type="rectangle|rounded|banner", text, width_inches, color)

TABLES:
insert_table(rows, cols, headers=[])
format_table(style)
set_table_cell_color(table_index, row, col, color)
set_table_header_color(table_index, color)
set_table_borders(table_index, border_color, border_size)
merge_table_cells(table_index, start_row, start_col, end_row, end_col)
set_column_width(table_index, col, width_inches)
add_table_row(table_index, data=[])
delete_table_row(table_index, row_index)
caption_table(table_index, caption_text, label)
sort_table(table_index, col, ascending)
set_table_cell_alignment(table_index, row, col, alignment)
set_table_row_height(table_index, row_index, height_inches)

REFERENCES:
add_table_of_contents(title, max_level, clickable=true)
add_table_of_figures(title, label)
add_index(entries=[], title)
add_bookmark(name, find_text)
add_cross_reference(bookmark_name, find_text, reference_type="page|text")
add_internal_link(link_text, target_heading, find_in_para)
link_all_headings()
add_footnote(find_text, footnote_text)
add_endnote(find_text, endnote_text)
add_hyperlink(text, url, find_text)

DOCUMENT ELEMENTS:
add_watermark(text)
remove_watermark()
add_cover_page(title, subtitle, author, date)
insert_text_box(text, width_inches)
insert_math_equation(equation)
format_code_block(find_text)
remove_comments()
add_comment(find_text, comment_text)
add_horizontal_line(before_headings, color)

CITATIONS:
add_citation(find_text, author, year, style="APA|MLA|IEEE")
add_bibliography(references=[], style)
add_mail_merge_field(field_name, find_text)

LAYOUT:
add_section_break(break_type="next_page|continuous|even_page|odd_page")
set_columns(num_columns, spacing_inches)
set_chapter_new_page()
add_page_border(style, color)
remove_page_border()

STYLES:
create_custom_style(style_name, base_style, font_name, font_size, bold, color)
apply_custom_style(style_name, find_text, apply_to_all)
apply_style_set(style_set="formal|casual|professional|elegant|minimalist")
set_document_properties(title, author, subject, keywords)
apply_heading_numbering(style="1.1.1")
remove_heading_numbers()
apply_heading_styles()

ACADEMIC FORMATS:
apply_sppu_format()
apply_apa_format()
apply_ieee_format()
apply_mla_format()
apply_resume_format()
apply_chicago_format()
apply_thesis_format()

PROTECTION:
set_password_protection(password, protection_type="read_only|forms")
remove_password_protection()
convert_to_pdf()

MAINTENANCE:
clear_document()
clean_empty_paragraphs()
normalize_spacing()

FORMAT SPECS:
- SPPU: TNR 12pt body justified 1.5 spacing 1cm indent | H1: 14pt bold centred | H2/H3: 12pt bold | L=1.5in R=1.0in T=B=1.0in | A4
- IEEE: TNR 10pt body justified single spacing 0.2in indent | Title 24pt bold centred | H2 10pt bold | T=0.75in B=1.57in L=R=0.59in | 2-col 4mm gap | A4
- APA: TNR 12pt double spacing left 1in margins 0.5in indent Letter
- MLA: TNR 12pt double spacing left 1in margins 0.5in indent Letter
- Resume: Calibri 11pt 1.15 spacing 0.75in margins dark green headings Letter
- Chicago: TNR 12pt double spacing 1in margins 0.5in indent Letter
- Thesis: TNR 12pt 1.5 spacing justified 1.5in left binding margin A4

EXAMPLES:
"make all headings bold" -> {"actions":[{"type":"set_heading_style","params":{"bold":true}}],"summary":"Made all headings bold"}
"justify all text" -> {"actions":[{"type":"set_alignment","params":{"alignment":"justify","apply_to":"all"}}],"summary":"Text justified"}
"set font Times New Roman 12pt" -> {"actions":[{"type":"set_font","params":{"font_name":"Times New Roman","size":12,"apply_to":"all"}}],"summary":"Font set"}
"make headings underlined black" -> {"actions":[{"type":"set_heading_style","params":{"bold":true,"color":"#000000","underline":true}}],"summary":"Headings underlined in black"}
"add table of contents" -> {"actions":[{"type":"add_table_of_contents","params":{"title":"Table of Contents","max_level":3,"clickable":true}}],"summary":"TOC added"}
"apply SPPU format" -> {"actions":[{"type":"apply_sppu_format","params":{}}],"summary":"SPPU format applied"}
"highlight all headings yellow" -> {"actions":[{"type":"set_highlight","params":{"color":"yellow","apply_to":"headings"}}],"summary":"Headings highlighted yellow"}
"add page numbers at bottom right" -> {"actions":[{"type":"add_page_numbers","params":{"position":"footer","alignment":"right","format":"Page X"}}],"summary":"Page numbers added"}
"insert warning box" -> {"actions":[{"type":"insert_highlight_box","params":{"text":"Warning message here","box_type":"warning"}}],"summary":"Warning box inserted"}
"apply IEEE format" -> {"actions":[{"type":"apply_ieee_format","params":{}}],"summary":"IEEE format applied"}
"make all text justified" -> {"actions":[{"type":"set_alignment","params":{"alignment":"justify","apply_to":"all"}}],"summary":"All text justified"}
"add header with Problem Statement" -> {"actions":[{"type":"add_header","params":{"text":"Problem Statement","alignment":"center"}}],"summary":"Header added"}
"link all headings" -> {"actions":[{"type":"link_all_headings","params":{}}],"summary":"All headings linked"}
"set line spacing to 1.5" -> {"actions":[{"type":"set_paragraph_spacing","params":{"line_spacing":1.5,"apply_to":"all"}}],"summary":"Line spacing set to 1.5"}
"make font size 12" -> {"actions":[{"type":"set_font","params":{"size":12,"apply_to":"all"}}],"summary":"Font size set to 12"}

RULES:
1. Return ONLY valid JSON, nothing else, no markdown backticks
2. Use hex colors like #000000 for black, #FF0000 for red
3. apply_to values: "all", "headings", "body"
4. alignment values: "left", "center", "right", "justify"
5. For clickable TOC always set clickable=true
6. For "add header with text X" use add_header with that exact text
7. For "link all headings" use link_all_headings action
8. For shadow/glow boxes use insert_styled_box
9. For note/warning/tip boxes use insert_highlight_box
10. If unsure pick the closest matching action, never return empty actions array
"""


def parse_command(command: str) -> dict:
    try:
        print(f"\n[PARSER] Command: {command}")

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": command}
            ],
            temperature=0.1,
            max_tokens=500,
        )

        content = response.choices[0].message.content.strip()
        print(f"[PARSER] Response: {content}")

        # Clean markdown fences
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        # Extract JSON object
        start = content.find('{')
        end   = content.rfind('}') + 1
        if start != -1 and end > start:
            content = content[start:end]

        parsed = json.loads(content)
        print(f"[PARSER] Parsed OK: {len(parsed.get('actions', []))} action(s)")
        return parsed

    except json.JSONDecodeError as e:
        print(f"[PARSER] JSON error: {e}")
        return {
            "actions": [],
            "summary": "Could not parse command. Please try rephrasing.",
            "error": True
        }
    except Exception as e:
        print(f"[PARSER] Exception: {type(e).__name__}: {e}")
        traceback.print_exc()
        return {
            "actions": [],
            "summary": f"Error: {str(e)}",
            "error": True
        }