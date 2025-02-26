# AI Resume Optimizer

An intelligent resume optimization tool that analyzes and enhances resumes based on job descriptions using AI.

## Features

- Resume parsing (PDF, DOCX)
- AI-powered document structure analysis
- Job description-based resume optimization
- Detailed improvement suggestions
- Professional formatting recommendations

## Prerequisites

- Python 3.8+
- Ollama (local AI model server)
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-resume
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up Ollama:
- Install Ollama following instructions at https://ollama.ai/
- Pull the required model:
```bash
ollama pull mistral
```

## Configuration

1. Create a `.env` file in the project root:
```
FLASK_ENV=production
FLASK_APP=app.py
SECRET_KEY=your-secret-key
LOG_LEVEL=INFO
```

2. Configure logging by creating `logging_config.ini`:
```ini
[loggers]
keys=root,app

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=defaultFormatter

[logger_root]
level=INFO
handlers=consoleHandler

[logger_app]
level=INFO
handlers=fileHandler
qualname=app
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=defaultFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=INFO
formatter=defaultFormatter
args=('logs/app.log', 'a')

[formatter_defaultFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
datefmt=%Y-%m-%d %H:%M:%S
```

## Development

Run the development server:
```bash
flask run --debug
```

## Production Deployment

1. Set up your production environment:
```bash
export FLASK_ENV=production
export FLASK_APP=app.py
```

2. Use Gunicorn for production:
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Docker Deployment (Optional)

1. Build the Docker image:
```bash
docker build -t ai-resume-optimizer .
```

2. Run the container:
```bash
docker run -d -p 8000:8000 ai-resume-optimizer
```

## Maintenance

- Monitor logs in `logs/app.log`
- Regularly update dependencies
- Check Ollama model updates

## Security Considerations

- Keep your `.env` file secure and never commit it
- Regularly update dependencies for security patches
- Use HTTPS in production
- Implement rate limiting for API endpoints

## Troubleshooting

Common issues and solutions:

1. Ollama connection errors:
   - Ensure Ollama service is running
   - Check if the model is properly downloaded

2. PDF parsing issues:
   - Verify PDF file permissions
   - Check file encoding

3. Memory issues:
   - Adjust Gunicorn worker settings
   - Monitor system resources

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## API Documentation

### Endpoints

#### 1. Upload Resume
```http
POST /upload
Content-Type: multipart/form-data
```

**Request Body:**
- `resume` (file, required): PDF, DOCX, or TXT file
  - Maximum file size: 16MB
  - Supported formats: `.pdf`, `.docx`, `.txt`

**Response:**
- Success (200):
```json
{
    "status": "success",
    "redirect": "/result"
}
```
- Error (400):
```json
{
    "error": "Invalid file type",
    "message": "Please upload a PDF, DOCX, or TXT file"
}
```

#### 2. Optimize Resume
```http
POST /optimize
Content-Type: application/x-www-form-urlencoded
```

**Request Body:**
- `job_description` (string, required): Job description text

**Response:**
- Success (200): HTML content with optimization results
- Error (400):
```json
{
    "error": "Missing data",
    "message": "Please provide a job description"
}
```

#### 3. Fetch Job Description
```http
POST /fetch_job_description
Content-Type: application/json
```

**Request Body:**
```json
{
    "url": "https://example.com/job-posting"
}
```

**Response:**
- Success (200):
```json
{
    "description": "Extracted job description text"
}
```
- Error (400):
```json
{
    "error": "Invalid URL or unable to extract description"
}
```

#### 4. Health Check
```http
GET /health
```

**Response:**
- Success (200):
```json
{
    "status": "OK"
}
```

### Error Codes

| Code | Description |
|------|-------------|
| 200  | Success |
| 400  | Bad Request - Invalid input |
| 401  | Unauthorized - Authentication required |
| 403  | Forbidden - Insufficient permissions |
| 404  | Not Found - Resource doesn't exist |
| 413  | Payload Too Large - File size exceeds limit |
| 500  | Internal Server Error |

### Rate Limiting

- 100 requests per hour per IP address
- 5 file uploads per minute per IP address

### Session Management

- Session duration: 30 minutes
- Session data stored server-side
- Session includes:
  - Original file type
  - Original filename
  - Parsed text content
  - Formatting information
  - Optimization results

### Example Usage

#### Upload Resume (cURL)
```bash
curl -X POST \
  -F "resume=@/path/to/resume.pdf" \
  http://your-domain.com/upload
```

#### Optimize Resume (cURL)
```bash
curl -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "job_description=Senior Software Engineer position..." \
  http://your-domain.com/optimize
```

#### Fetch Job Description (cURL)
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/job-posting"}' \
  http://your-domain.com/fetch_job_description
```

### Security Considerations

1. **File Upload Security**
   - File size limit: 16MB
   - Allowed extensions: `.pdf`, `.docx`, `.txt`
   - Secure filename handling
   - Content type validation

2. **API Security**
   - CSRF protection enabled
   - Rate limiting
   - Input sanitization
   - Secure session handling

3. **Data Privacy**
   - Uploaded files are processed and immediately deleted
   - No permanent storage of resume content
   - Session data expires after 30 minutes

### Development Integration

#### Python Example
```python
import requests

# Upload resume
files = {'resume': open('resume.pdf', 'rb')}
upload_response = requests.post('http://your-domain.com/upload', files=files)

# Optimize resume
job_description = "Senior Software Engineer position..."
optimize_response = requests.post(
    'http://your-domain.com/optimize',
    data={'job_description': job_description}
)

# Fetch job description
url_response = requests.post(
    'http://your-domain.com/fetch_job_description',
    json={'url': 'https://example.com/job-posting'}
)
```

#### JavaScript Example
```javascript
// Upload resume
const formData = new FormData();
formData.append('resume', fileInput.files[0]);

fetch('/upload', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data));

// Optimize resume
fetch('/optimize', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
        'job_description': 'Senior Software Engineer position...'
    })
})
.then(response => response.text())
.then(html => console.log(html));

// Fetch job description
fetch('/fetch_job_description', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        url: 'https://example.com/job-posting'
    })
})
.then(response => response.json())
.then(data => console.log(data));
```