import json
import traceback
from groq import Groq
from app.core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

SYSTEM_PROMPT = """You convert document editing commands to JSON.

Respond ONLY with this JSON format, nothing else:
{"actions": [{"type": "action_name", "params": {}}], "summary": "what was done"}

ACTIONS:
set_font(font_name, size, bold, italic, color, apply_to, find_text)
set_heading_style(level, bold, color, font_size)
apply_heading_styles()
set_alignment(alignment, apply_to, find_text)
set_margins(top, bottom, left, right)
set_paragraph_spacing(before, after, line_spacing, apply_to)
set_underline(apply_to, find_text)
set_strikethrough(apply_to, find_text)
set_highlight(color, find_text, apply_to)
search_and_highlight(find_text, color)
remove_highlight(apply_to)
set_text_color(color, apply_to, find_text)
set_indent(left, right, first_line, apply_to)
remove_formatting(apply_to)
set_text_case(case, apply_to)
copy_formatting(source_text, target_text)
set_paragraph_shading(color, apply_to)
set_paragraph_border(style, color, sides)
set_text_effect(find_text, effect)
remove_text_effects(find_text)
replace_font(old_font, new_font)
enable_track_changes()
disable_track_changes()
accept_all_changes()
reject_all_changes()
find_replace(find, replace, case_sensitive)
add_text(text, position, new_paragraph)
delete_text(find)
count_words()
count_paragraphs()
add_bullet_list(items)
add_numbered_list(items)
add_checklist(items)
convert_to_bullets()
convert_to_checklist()
add_page_break()
add_blank_page()
set_page_size(size)
set_page_orientation(orientation)
set_page_color(color)
add_line_numbers(start, step, restart)
remove_line_numbers()
set_page_number_start(start)
add_header(text, alignment)
add_footer(text, alignment)
remove_header()
remove_footer()
add_page_numbers(position, alignment, format)
set_different_first_page_header(first_header, rest_header)
insert_date_field()
insert_page_count_field(position)
insert_image(image_path, width_inches, alignment, caption)
insert_image_with_border(image_path, width_inches, border_color)
caption_image(image_index, caption_text, label)
insert_styled_box(text, style, color, width_inches)
insert_highlight_box(text, box_type)
insert_divider(style, color)
insert_badge(text, color)
insert_smartart(type, items, title)
insert_shape_text(shape_type, text, color)
insert_table(rows, cols, headers)
format_table(style)
set_table_cell_color(table_index, row, col, color)
set_table_header_color(table_index, color)
set_table_borders(table_index, border_color, border_size)
merge_table_cells(table_index, start_row, start_col, end_row, end_col)
add_table_row(table_index, data)
delete_table_row(table_index, row_index)
sort_table(table_index, col, ascending)
add_table_of_contents(title, max_level, clickable)
add_table_of_figures(title, label)
add_bookmark(name, find_text)
add_internal_link(link_text, target_heading, find_in_para)
link_all_headings()
add_footnote(find_text, footnote_text)
add_endnote(find_text, endnote_text)
add_hyperlink(text, url, find_text)
add_watermark(text)
remove_watermark()
add_cover_page(title, subtitle, author, date)
insert_text_box(text, width_inches)
insert_math_equation(equation)
format_code_block(find_text)
add_comment(find_text, comment_text)
add_horizontal_line(before_headings, color)
add_citation(find_text, author, year, style)
add_bibliography(references, style)
add_section_break(break_type)
set_columns(num_columns, spacing_inches)
set_chapter_new_page()
add_page_border(style, color)
remove_page_border()
apply_style_set(style_set)
apply_heading_numbering(style)
remove_heading_numbers()
apply_sppu_format()
apply_apa_format()
apply_ieee_format()
apply_mla_format()
apply_resume_format()
apply_chicago_format()
apply_thesis_format()
set_password_protection(password, protection_type)
remove_password_protection()
clean_empty_paragraphs()
normalize_spacing()

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

RULES:
1. Return ONLY valid JSON, nothing else, no markdown
2. Use hex colors like #000000
3. apply_to values: "all", "headings", "body"
4. alignment values: "left", "center", "right", "justify"
5. If unsure, pick the closest matching action
"""


def parse_command(command: str) -> dict:
    try:
        print(f"\n[PARSER] Received command: {command}")
        print(f"[PARSER] Using API key: {settings.GROQ_API_KEY[:8]}...")

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
        print(f"[PARSER] Raw response: {content}")

        # Clean markdown fences if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        # Find JSON object in response
        start = content.find('{')
        end   = content.rfind('}') + 1
        if start != -1 and end > start:
            content = content[start:end]

        parsed = json.loads(content)
        print(f"[PARSER] Parsed successfully: {parsed}")
        return parsed

    except json.JSONDecodeError as e:
        print(f"[PARSER] JSON parse error: {e}")
        print(f"[PARSER] Raw content was: {content if 'content' in dir() else 'N/A'}")
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