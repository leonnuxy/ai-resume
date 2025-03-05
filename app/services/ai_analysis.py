import json
import ollama
import logging.config
import os
import time
from typing import Dict, Optional
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

# Configure logging
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                          'instance', 'logs', 'logging_config.ini')
logging.config.fileConfig(config_path)
logger = logging.getLogger('analysis')
logger.setLevel(logging.DEBUG)  # Set to DEBUG level

# Constants
LOG_SENDING_PROMPT = "Sending prompt to Ollama"

def retry_on_connection_error(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry functions on connection errors."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))  # Exponential backoff
            logger.error(f"All attempts failed: {str(last_error)}")
            raise last_error
        return wrapper
    return decorator

def _validate_analysis_response(response: Dict) -> bool:
    """Validate that the response contains all required fields in the correct format."""
    required_keys = ['missing_skills', 'improvement_suggestions', 'emphasis_suggestions', 'general_suggestions']
    
    if not all(key in response for key in required_keys):
        return False
    
    try:
        # Validate missing_skills structure
        if not isinstance(response['missing_skills'], list):
            return False
        for skill in response['missing_skills']:
            if not isinstance(skill, dict) or 'skill' not in skill or 'suggestion' not in skill:
                return False
        
        # Validate improvement_suggestions structure
        if not isinstance(response['improvement_suggestions'], list):
            return False
        for suggestion in response['improvement_suggestions']:
            if not isinstance(suggestion, dict) or 'current' not in suggestion or 'suggested' not in suggestion or 'reason' not in suggestion:
                return False
        
        # Validate emphasis_suggestions structure
        if not isinstance(response['emphasis_suggestions'], list):
            return False
        for emphasis in response['emphasis_suggestions']:
            if not isinstance(emphasis, dict) or 'experience' not in emphasis or 'why_relevant' not in emphasis or 'how_to_emphasize' not in emphasis:
                return False
        
        # Validate general_suggestions structure
        if not isinstance(response['general_suggestions'], list):
            return False
        for suggestion in response['general_suggestions']:
            if not isinstance(suggestion, str):
                return False
                
        return True
    except Exception:
        return False

@retry_on_connection_error()
def _send_ollama_request(prompt: str, timeout: int = 300) -> Optional[Dict]:
    """Send a request to Ollama with retry logic and timeout."""
    logger.debug(f"Sending request to Ollama with prompt: {prompt[:100]}...")

    def execute_request():
        try:
            response = ollama.chat(
                model='mistral',
                messages=[{
                    'role': 'user',
                    'content': prompt
                }],
                stream=True  # Enable streaming for progress updates
            )
            
            # Accumulate streamed response
            full_response = ""
            for chunk in response:
                if chunk and 'message' in chunk and 'content' in chunk['message']:
                    full_response += chunk['message']['content']
                    # Log progress for monitoring
                    logger.debug(f"Received chunk: {chunk['message']['content'][:50]}...")
            
            logger.debug(f"Raw Ollama response: {full_response}")
            
            if not full_response.strip():
                logger.error("Empty response received from Ollama")
                raise ValueError("Empty response received from Ollama")
            
            try:
                # Try to find JSON content within the response
                json_start = full_response.find('{')
                json_end = full_response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_content = full_response[json_start:json_end]
                    parsed_response = json.loads(json_content)
                else:
                    parsed_response = json.loads(full_response)
                
                # Check if the response is empty
                if not parsed_response:
                    logger.error("Parsed response is empty")
                    raise ValueError("Empty JSON response from Ollama")
                
                logger.info(f"Successfully parsed JSON response: {parsed_response}")
                
                # Validate the response format
                if _validate_analysis_response(parsed_response):
                    return parsed_response
                else:
                    logger.error("Invalid response format")
                    raise ValueError("Invalid response format from Ollama")
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse or validate response: {str(e)}")
                logger.error(f"Raw content that failed to parse: {full_response}")
                return {
                    "missing_skills": [{
                        "skill": "ERROR",
                        "suggestion": "Analysis failed due to invalid response format"
                    }],
                    "improvement_suggestions": [{
                        "current": "ERROR",
                        "suggested": "Please try again",
                        "reason": "Invalid response received from AI"
                    }],
                    "emphasis_suggestions": [{
                        "experience": "ERROR",
                        "why_relevant": "Invalid response format",
                        "how_to_emphasize": "Please try the analysis again"
                    }],
                    "general_suggestions": [
                        "The analysis failed due to an invalid response format. Please try again.",
                        "If the problem persists, try with a shorter resume or job description."
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error in Ollama request: {str(e)}", exc_info=True)
            raise

    # Execute with timeout
    with ThreadPoolExecutor(max_workers=1) as executor:
        try:
            future = executor.submit(execute_request)
            return future.result(timeout=timeout)
        except FuturesTimeoutError:
            logger.error(f"Ollama request timed out after {timeout} seconds")
            raise TimeoutError(f"Request timed out after {timeout} seconds")

def analyze_resume_sections(text: str) -> Dict:
    """Analyze the sections of a resume using AI."""
    try:
        logger.info("Starting resume sections analysis")
        prompt = f"""Analyze this resume and identify its sections:

        RESUME:
        {text}

        Format your response as a JSON object with these exact keys:
        {{
            "sections": [
                {{
                    "name": "section name (e.g., Education, Experience)",
                    "content": "section content",
                    "formatting": {{
                        "is_header": true,
                        "suggested_font_size": 14
                    }}
                }}
            ]
        }}"""

        return _send_ollama_request(prompt) or {"sections": []}

    except Exception as e:
        logger.error(f"Error in resume sections analysis: {str(e)}", exc_info=True)
        return {"sections": []}

def analyze_document_structure(text: str) -> Dict:
    """Analyze the structure of a document using AI."""
    try:
        logger.info("Starting document structure analysis")
        prompt = f"""Analyze this document's structure and identify its sections:

        DOCUMENT:
        {text}

        Format your response as a JSON object with these exact keys:
        {{
            "sections": [
                {{
                    "name": "section name",
                    "content": "section content",
                    "formatting": {{
                        "is_header": boolean,
                        "suggested_font_size": number
                    }}
                }}
            ]
        }}"""

        return _send_ollama_request(prompt) or {"sections": []}

    except Exception as e:
        logger.error(f"Error in document structure analysis: {str(e)}", exc_info=True)
        return {"sections": []}

def analyze_resume_for_job(resume_text: str, job_description: str, timeout: int = 300) -> Dict:
    """Analyze and optimize resume for a specific job."""
    if not resume_text or not job_description:
        logger.warning("Empty resume text or job description provided")
        return {
            "missing_skills": [],
            "improvement_suggestions": [],
            "emphasis_suggestions": [],
            "general_suggestions": ["No resume text or job description provided"]
        }
    
    try:
        logger.info("Starting resume optimization analysis")
        prompt = f"""You are a professional resume optimization expert. Analyze the resume against the job description and provide feedback in valid JSON format.

Input Resume:
{resume_text}

Job Description:
{job_description}

Instructions:
1. Compare the resume against the job requirements
2. Identify missing skills and gaps
3. Suggest improvements for existing content
4. Identify relevant experiences to emphasize
5. Provide general optimization suggestions

Return ONLY a JSON object with this EXACT structure, no other text:
{{
    "missing_skills": [
        {{
            "skill": "specific required skill that is missing",
            "suggestion": "detailed suggestion on how to address this gap"
        }}
    ],
    "improvement_suggestions": [
        {{
            "current": "exact text from resume that needs improvement",
            "suggested": "improved version of the text",
            "reason": "explanation of why this improves the match"
        }}
    ],
    "emphasis_suggestions": [
        {{
            "experience": "relevant experience from the resume",
            "why_relevant": "explanation of relevance to job requirements",
            "how_to_emphasize": "specific suggestion on how to emphasize this"
        }}
    ],
    "general_suggestions": [
        "actionable suggestion 1",
        "actionable suggestion 2"
    ]
}}"""
        
        logger.debug(f"Sending prompt to Ollama")
        response = _send_ollama_request(prompt, timeout=timeout)
        logger.debug(f"Received response from Ollama")
        
        if not response or not isinstance(response, dict):
            logger.error("Invalid or empty response from Ollama")
            return {
                "missing_skills": [{
                    "skill": "Error analyzing resume",
                    "suggestion": "Please try again with more detailed content"
                }],
                "improvement_suggestions": [],
                "emphasis_suggestions": [],
                "general_suggestions": [
                    "Analysis failed - Please ensure your resume and job description are detailed enough",
                    "Try providing more specific details in both the resume and job requirements"
                ]
            }
            
        return response
        
    except TimeoutError as e:
        logger.error(f"Analysis timed out: {str(e)}")
        return {
            "missing_skills": [],
            "improvement_suggestions": [],
            "emphasis_suggestions": [],
            "general_suggestions": [f"Analysis timed out after {timeout} seconds. Please try again with shorter content."]
        }
    except Exception as e:
        logger.error(f"Error in resume optimization analysis: {str(e)}", exc_info=True)
        return {
            "missing_skills": [],
            "improvement_suggestions": [],
            "emphasis_suggestions": [],
            "general_suggestions": ["An error occurred during analysis. Please try again."]
        }

def test_ollama_connection() -> bool:
    """Test the connection to Ollama service."""
    try:
        logger.info("Testing Ollama connection")
        response = ollama.chat(model='mistral', messages=[{
            'role': 'user',
            'content': 'Hi, this is a test message. Please respond with "OK" if you receive this.'
        }])
        
        if response and response.get('message') and response['message'].get('content'):
            logger.info("Successfully connected to Ollama")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to connect to Ollama: {str(e)}")
        return False

# Ensure the function is exported
__all__ = ['analyze_resume_for_job', 'analyze_document_structure', 'analyze_resume_sections', 'test_ollama_connection']
