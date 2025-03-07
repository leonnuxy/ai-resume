from docx import Document
from typing import List, Tuple
from app.utils.text_cleaner import clean_text

# Reuse categorize_sections, identify_name_and_group_sections, and format_sections from pdf_parser
from app.parsers.pdf_parser import categorize_sections, identify_name_and_group_sections, format_sections

def parse_docx(file_path: str) -> Tuple[str, str]:
    """Parse DOCX file and extract text and formatting"""
    doc = Document(file_path)
    text = ""
    all_words = []
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
        for run in paragraph.runs:
            word = {
                'text': run.text,
                'font_size': run.font.size.pt if run.font.size else 10,
                'top': 0,  # DOCX does not provide positional information
                'bottom': 0  # DOCX does not provide positional information
            }
            all_words.append(word)
    line_spacing = {}  # DOCX does not provide positional information
    sections = categorize_sections(all_words, line_spacing)
    name, grouped_sections = identify_name_and_group_sections(sections)
    formatted_sections = format_sections(grouped_sections)
    cleaned_text = clean_text(text)
    return cleaned_text, formatted_sections
