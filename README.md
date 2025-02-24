# Resume Parser

A simple web application that parses resumes in PDF, DOCX, or TXT format and displays the content in a structured format.

## Features

- Upload resume files (PDF, DOCX, or TXT)
- Parse resume content into sections
- Display parsed content in a clean, organized format
- Basic error handling
- Responsive design

## Requirements

- Python 3.7+
- Flask
- PyPDF2
- python-docx

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd resume-parser
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage

1. Visit the homepage
2. Click the "Choose File" button to select your resume
3. Click "Parse Resume" to upload and process the file
4. View the parsed resume sections on the results page

## Supported File Types

- PDF (.pdf)
- Microsoft Word (.docx)
- Text files (.txt)

## File Size Limit

The maximum file size is 16MB.

## Error Handling

The application includes basic error handling for:
- Invalid file types
- File size limits
- File processing errors

## License

MIT License