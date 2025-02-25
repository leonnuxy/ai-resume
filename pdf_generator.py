from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate
from reportlab.lib.utils import simpleSplit
import io
from typing import Dict, Tuple, BinaryIO

def apply_text_formatting(text: str, format_info: dict) -> tuple:
    """Apply formatting to text and return font settings."""
    font_size = format_info.get('size', 10)
    spacing = format_info.get('spacing', 2)
    is_header = format_info.get('is_header', False)
    font_name = "Helvetica-Bold" if is_header else "Helvetica"
    return font_name, font_size, spacing

def get_text_format(line: str, text_format_map: dict, default_font_size: int = 10) -> dict:
    """Get formatting for a line of text."""
    for original_text, format_info in text_format_map.items():
        if line.strip() in original_text or original_text in line.strip():
            return format_info
    return {'size': default_font_size, 'spacing': 2, 'is_header': False}

def draw_text_line(canvas, line: str, y: float, margin: int, font_name: str, font_size: float) -> float:
    """Draw a line of text and return new y position."""
    if not line.strip():
        return y - font_size
    
    canvas.setFont(font_name, font_size)
    text_width = canvas.stringWidth(line)
    x = (letter[0] - text_width) / 2  # Center the text
    canvas.drawString(x, y, line)
    return y

def process_formatted_text(c, text: str, text_format_map: dict, y: float, margin: int, default_font_size: int) -> float:
    """Process text with formatting and return new y position."""
    for line in text.split('\n'):
        if y < 25:  # Reduced from 50 to match the smaller font sizes
            c.showPage()
            y = 750
        
        format_info = get_text_format(line, text_format_map, default_font_size)
        font_name, font_size, spacing = apply_text_formatting(line, format_info)
        y = draw_text_line(c, line, y, margin, font_name, font_size)
        y -= (font_size + spacing)
    return y

def process_simple_text(c, text: str, y: float, margin: int, default_font_size: int) -> float:
    """Process text without formatting and return new y position."""
    for line in text.split('\n'):
        if y < 25:  # Reduced from 50 to match the smaller font sizes
            c.showPage()
            y = 750
            c.setFont("Helvetica", default_font_size)
        
        y = draw_text_line(c, line, y, margin, "Helvetica", default_font_size)
        y -= (default_font_size + 2)
    return y

def create_formatted_pdf(text: str, formatting: dict = None) -> Tuple[BinaryIO, str]:
    """Create a formatted PDF from text with optional formatting."""
    file_data = io.BytesIO()
    c = canvas.Canvas(file_data, pagesize=letter)
    y = 750
    margin = 36  # Reduced from 72 to match the smaller font sizes
    default_font_size = 5  # Reduced from 10 to match the smaller font sizes
    
    if formatting and 'sections' in formatting:
        # Use AI section analysis for better formatting
        section_analysis = formatting.get('section_analysis', {})
        section_order = section_analysis.get('structure_analysis', {}).get('section_order', [])
        
        # Create formatting map with AI insights
        text_format_map = {}
        for section in formatting['sections']:
            ai_section = next(
                (s for s in section_analysis.get('sections', []) 
                 if s['name'].lower() in section['text'].lower()),
                None
            )
            
            text_format_map[section['text']] = {
                'size': section['font_size'] / 2 * (1.2 if ai_section and ai_section['formatting']['is_header'] else 1),
                'spacing': formatting['line_spacing'].get(section['text'], 2),
                'is_header': ai_section['formatting']['is_header'] if ai_section else False
            }
        
        # Process text with improved section handling
        paragraphs = text.split('\n\n')
        for paragraph in paragraphs:
            y = process_formatted_text(c, paragraph, text_format_map, y, margin, default_font_size)
            y -= 10  # Reduced from 20 to match the smaller font sizes
    else:
        c.setFont("Helvetica", default_font_size)
        for paragraph in text.split('\n\n'):
            y = process_simple_text(c, paragraph, y, margin, default_font_size)
            y -= 10  # Reduced from 20 to match the smaller font sizes
    
    c.save()
    file_data.seek(0)
    return file_data, 'application/pdf' 