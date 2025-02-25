import pdfplumber
import PyPDF2
from docx import Document
from typing import Dict, List, Tuple

def process_word(word: dict, base_size: float = None) -> dict:
    """Process a single word and return its formatting."""
    if not word['text'].strip():
        return {}
    
    size = word['size']
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

def extract_pdf_formatting(file_path: str) -> dict:
    """Extract formatting information from a PDF file."""
    from analysis import analyze_document_structure, analyze_resume_sections
    
    formatting = {
        'sections': [],
        'default_font_size': 10,
        'line_spacing': {},
        'ai_analysis': None,
        'section_analysis': None
    }
    
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                words = page.extract_words(keep_blank_chars=True)
                text += page.extract_text() + "\n"
                
                sizes = [word['size'] for word in words if word['text'].strip()]
                base_size = sorted(set(sizes), key=sizes.count)[-1] if sizes else None
                
                for word in words:
                    section = process_word(word, base_size)
                    if section:
                        formatting['sections'].append(section)
            
            # Get AI analysis of document structure and sections
            formatting['ai_analysis'] = analyze_document_structure(text)
            formatting['section_analysis'] = analyze_resume_sections(text)
            formatting['line_spacing'] = calculate_line_spacing(formatting['sections'])
            
            # Apply AI section analysis to improve formatting
            if formatting['section_analysis'] and 'sections' in formatting['section_analysis']:
                for section in formatting['section_analysis']['sections']:
                    # Find matching text in formatting sections
                    for fmt_section in formatting['sections']:
                        if section['name'].lower() in fmt_section['text'].lower():
                            fmt_section['is_header'] = section['formatting']['is_header']
                            fmt_section['font_size'] = max(fmt_section['font_size'], 
                                                         section['formatting']['suggested_font_size'])
                            
    except Exception as e:
        print(f"Error extracting formatting: {str(e)}")
    
    return formatting

def parse_pdf(file_path: str) -> Tuple[str, dict]:
    """Parse PDF and extract both text and formatting"""
    text = ""
    formatting = extract_pdf_formatting(file_path)
    
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    
    return text, formatting

def parse_docx(file_path: str) -> str:
    """Parse DOCX file and extract text"""
    doc = Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def parse_txt(file_path: str) -> str:
    """Parse TXT file and extract text"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read() 