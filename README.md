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