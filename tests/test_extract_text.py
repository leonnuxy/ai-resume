import os
import sys
# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.resume_parser import parse_pdf

def test_extract_text_from_pdf():
    file_path = os.path.join(os.path.dirname(__file__), 'resume.pdf')
    text, formatting = parse_pdf(file_path)
    print("Extracted Text:")
    print(text)

if __name__ == '__main__':
    test_extract_text_from_pdf()
