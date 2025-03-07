import pdfplumber
from typing import List, Tuple
from app.services.ai_analysis import analyze_document_structure, analyze_resume_sections

def process_word(word: dict, base_size: float = None) -> dict:
    """Process a single word and return its formatting."""
    if not word['text'].strip():
        return {}
    
    size = word.get('size', base_size)  # Use base_size as default if size is missing
    normalized_size = round((size / base_size) * 10, 1) if base_size else 10
    
    return {
        'text': word['text'].strip(),
        'font_size': normalized_size,
        'top': word['top'],
        'bottom': word['bottom']
    }

def calculate_line_spacing(sections: list) -> dict:
    """Calculate line spacing between sections."""
    spacing = {}
    sorted_sections = sorted(sections, key=lambda x: x['top'])
    
    for i in range(len(sorted_sections)-1):
        curr, next_sect = sorted_sections[i], sorted_sections[i+1]
        space = next_sect['top'] - curr['bottom']
        if space > 0:
            spacing[curr['text']] = min(space / 2, 10)
    
    return spacing

def categorize_sections(words: List[dict], line_spacing: dict) -> List[dict]:
    """Categorize the extracted words into sections based on formatting and line spacing."""
    sections = []
    current_section = {'title': '', 'content': []}
    for word in words:
        if word['text'] in line_spacing:
            if current_section['content']:
                sections.append(current_section)
                current_section = {'title': word['text'], 'content': []}
            else:
                current_section['title'] = word['text']
        current_section['content'].append(word)
    if current_section['content']:
        sections.append(current_section)
    return sections

def identify_name_and_group_sections(sections: List[dict]) -> Tuple[str, List[dict]]:
    """Identify the name and group sections into Skills, Experience, and Other."""
    name = ''
    grouped_sections = {'Skills': [], 'Experience': [], 'Other': []}
    for section in sections:
        title = section['title'].lower()
        if 'skills' in title:
            grouped_sections['Skills'].append(section)
        elif 'experience' in title:
            grouped_sections['Experience'].append(section)
        elif not name:
            name = ' '.join(word['text'] for word in section['content'])
        else:
            grouped_sections['Other'].append(section)
    return name, grouped_sections

def format_sections(grouped_sections: dict) -> str:
    """Format the grouped sections for display."""
    formatted_text = ""
    for group, sections in grouped_sections.items():
        formatted_text += f"\n{group}\n"
        for section in sections:
            formatted_text += f"\n{section['title']}\n"
            for word in section['content']:
                formatted_text += f"{word['text']} "
            formatted_text += "\n"
    return formatted_text.strip()

def parse_pdf(file_path: str) -> Tuple[str, str]:
    """Parse PDF and extract both text and formatting"""
    with pdfplumber.open(file_path) as pdf:
        pages = pdf.pages
        all_words = []
        for page in pages:
            words = page.extract_words()
            sizes = [word['size'] for word in words if 'size' in word and word['text'].strip()]
            base_size = min(sizes) if sizes else 10  # Set a default base size if no sizes are found
            processed_words = [process_word(word, base_size) for word in words if word['text'].strip()]
            all_words.extend(processed_words)
        line_spacing = calculate_line_spacing(all_words)
        sections = categorize_sections(all_words, line_spacing)
        name, grouped_sections = identify_name_and_group_sections(sections)
        text = ' '.join(word['text'] for word in all_words)
        formatted_sections = format_sections(grouped_sections)
        return text, formatted_sections
