"""
Module for analyzing and optimizing resumes using AI.
Provides functionality for document structure analysis and job-specific optimization.
"""

import json
import logging
import logging.config
from typing import Dict, List, Optional
import ollama
from pathlib import Path

# Configure logging
logging.config.fileConfig('logging_config.ini')
logger = logging.getLogger('analysis')

# Constants
LOG_SENDING_PROMPT = "Sending prompt to Ollama"

def analyze_document_structure(text: str) -> Dict:
    """
    Analyze document structure and provide formatting recommendations.
    
    Args:
        text: The document text to analyze
        
    Returns:
        Dict containing section analysis and formatting recommendations
    """
    try:
        logger.info("Starting document structure analysis")
        prompt = f"""Analyze this document and provide formatting recommendations in JSON format.
        Focus on:
        1. Identifying section headers
        2. Determining relative font sizes for different elements
        3. Suggesting spacing between sections
        4. Identifying key formatting patterns
        
        Document text:
        {text}
        
        Respond only with JSON in this format:
        {{
            "sections": [
                {{
                    "text": "section text",
                    "is_header": boolean,
                    "relative_size": float,
                    "spacing_after": float
                }}
            ],
            "base_font_size": float,
            "formatting_notes": string
        }}
        """
        
        logger.debug(LOG_SENDING_PROMPT)
        response = ollama.chat(model='mistral', messages=[{
            'role': 'user',
            'content': prompt
        }])
        
        analysis = json.loads(response['message']['content'])
        logger.info("Successfully completed document structure analysis")
        return analysis
    except Exception as e:
        logger.error(f"Error in document structure analysis: {str(e)}", exc_info=True)
        return {}

def analyze_resume_sections(text: str) -> Dict:
    """
    Analyze and identify resume sections.
    
    Args:
        text: The resume text to analyze
        
    Returns:
        Dict containing identified sections and their content
    """
    logger.info("Starting resume section analysis")
    
    # Define standard sections
    standard_sections = {
        'Skills': [
            '• Languages: Python, Java, C#, Go, Scala, C++, SQL, JavaScript(React) and HTML/CSS',
            '• Cloud & DevOps: Kubernetes, Google Cloud, Azure Kubernetes Services, AWS, Jenkins, Docker, and Kafka',
            '• Methodologies: Agile (Scrum), Continuous Integration/Continuous Deployment (CI/CD), Jira, Confluence, SDLC',
            '• Web Development: React, Selenium, REST APIs, Spring Boot, .NET, Node.js, PostgreSQL, MongoDB, MySQL',
            '• Data Analysis: Power BI, Tableau, Power Query, and advanced Microsoft Excel',
            '• Data Infrastructure: ETM deliverables, Snowflake, Azure Data Services, and Operational Data Store (ODS)'
        ],
        'Experience': [],
        'Achievements': [],
        'Education': [],
        'Certifications': []
    }

    try:
        logger.debug("Preparing prompt for section analysis")
        prompt = f"""Analyze this resume text and categorize it into standard sections. You must identify and categorize content into these specific sections:
        1. Skills (with subsections for different skill types)
        2. Experience
        3. Achievements
        4. Education
        5. Certifications

        Resume text:
        {text}

        Return the analysis in this JSON format:
        {{
            "sections": [
                {{
                    "name": "Skills",
                    "type": "main_section",
                    "content": ["List of identified skills with bullet points"],
                    "formatting": {{
                        "is_header": true,
                        "suggested_font_size": 12,
                        "suggested_spacing": 1.5
                    }}
                }}
            ]
        }}"""

        logger.debug(LOG_SENDING_PROMPT)
        response = ollama.chat(model='mistral', messages=[{
            'role': 'user',
            'content': prompt
        }])
        
        analysis = json.loads(response['message']['content'])
        logger.debug("Successfully parsed Ollama response")
        
        # Process sections
        sections = []
        for section_name, default_subsections in standard_sections.items():
            existing_section = next(
                (s for s in analysis.get('sections', []) if s['name'] == section_name),
                None
            )
            
            # Determine content based on section
            if section_name == 'Skills':
                content = default_subsections
            else:
                content = existing_section.get('content', []) if existing_section else []
            
            sections.append({
                'name': section_name,
                'type': 'main_section',
                'content': content,
                'formatting': {
                    'is_header': True,
                    'suggested_font_size': 12,
                    'suggested_spacing': 1.5
                }
            })
        
        result = {
            'sections': sections,
            'structure_analysis': {
                'section_order': list(standard_sections.keys()),
                'hierarchy': {
                    'main_sections': list(standard_sections.keys()),
                    'subsections': {}
                }
            }
        }
        
        logger.info("Successfully completed resume section analysis")
        return result
        
    except Exception as e:
        logger.error(f"Error in resume section analysis: {str(e)}", exc_info=True)
        # Return default structure on error
        return {
            'sections': [
                {
                    'name': name,
                    'type': 'main_section',
                    'content': content if name == 'Skills' else [],
                    'formatting': {
                        'is_header': True,
                        'suggested_font_size': 12,
                        'suggested_spacing': 1.5
                    }
                } for name, content in standard_sections.items()
            ],
            'structure_analysis': {
                'section_order': list(standard_sections.keys()),
                'hierarchy': {
                    'main_sections': list(standard_sections.keys()),
                    'subsections': {}
                }
            }
        }

def analyze_resume_for_job(resume_text: str, job_description: str) -> Dict:
    """
    Analyze and optimize resume for a specific job.
    
    Args:
        resume_text: The resume text to analyze
        job_description: The job description to compare against
        
    Returns:
        Dict containing optimization suggestions
    """
    if not resume_text or not job_description:
        logger.warning("Empty resume text or job description provided")
        return {}

    try:
        logger.info("Starting resume optimization analysis")
        prompt = f"""As a professional resume optimization expert, analyze this resume against the job description.
        
        RESUME:
        {resume_text}
        
        JOB DESCRIPTION:
        {job_description}
        
        Provide specific recommendations in these categories:
        1. Missing Skills/Experience
        2. Content Improvements
        3. Emphasis Opportunities
        4. General Suggestions

        Format your response as a JSON object with these exact keys:
        {{
            "missing_skills": [
                {{
                    "skill": "specific missing skill",
                    "suggestion": "how to address this gap"
                }}
            ],
            "improvement_suggestions": [
                {{
                    "current": "current text",
                    "suggested": "improved version",
                    "reason": "why this improves the match"
                }}
            ],
            "emphasis_suggestions": [
                {{
                    "experience": "relevant experience",
                    "why_relevant": "relevance to job",
                    "how_to_emphasize": "emphasis suggestion"
                }}
            ],
            "general_suggestions": [
                "specific actionable suggestion"
            ]
        }}"""

        logger.debug(LOG_SENDING_PROMPT)
        response = ollama.chat(model='mistral', messages=[{
            'role': 'user',
            'content': prompt
        }])
        
        if not response or not response.get('message') or not response['message'].get('content'):
            logger.error("Empty or invalid response from Ollama")
            return {}
        
        analysis = json.loads(response['message']['content'])
        logger.debug("Successfully parsed Ollama response")
        
        # Validate analysis structure
        required_keys = ['missing_skills', 'improvement_suggestions', 
                        'emphasis_suggestions', 'general_suggestions']
        
        if not all(key in analysis for key in required_keys):
            logger.warning("Missing required keys in analysis response")
            return {key: [] for key in required_keys}
        
        logger.info("Successfully completed resume optimization analysis")
        return analysis
            
    except Exception as e:
        logger.error(f"Error in resume optimization analysis: {str(e)}", exc_info=True)
        return {
            "missing_skills": [],
            "improvement_suggestions": [],
            "emphasis_suggestions": [],
            "general_suggestions": [
                "Unable to complete analysis. Please try again."
            ]
        }

def format_optimization_suggestions(analysis: Dict) -> str:
    """
    Format optimization suggestions into HTML.
    
    Args:
        analysis: Dict containing optimization suggestions
        
    Returns:
        Formatted HTML string containing the suggestions
    """
    if not analysis:
        return """
        <div class="optimization-results">
            <p>No specific suggestions found. Please try again with a more detailed job description.</p>
        </div>
        """
    
    def format_section(title: str, items: List, formatter_func) -> str:
        """Format a section of suggestions."""
        if not items:
            return ""
            
        formatted_items = [formatter_func(item) for item in items]
        return f"""
        <div class="suggestion-section">
            <h4>{title}</h4>
            <ul>
                {''.join(formatted_items)}
            </ul>
        </div>
        """
    
    # Format sections
    sections = {
        "Missing Key Skills": (
            analysis.get('missing_skills', []),
            lambda x: f"<li><strong>{x['skill']}</strong>: {x['suggestion']}</li>"
        ),
        "Suggested Improvements": (
            analysis.get('improvement_suggestions', []),
            lambda x: f"<li><strong>Current:</strong> {x['current']}<br>"
                     f"<strong>Suggested:</strong> {x['suggested']}<br>"
                     f"<em>Why:</em> {x['reason']}</li>"
        ),
        "Experiences to Emphasize": (
            analysis.get('emphasis_suggestions', []),
            lambda x: f"<li><strong>{x['experience']}</strong><br>"
                     f"<em>Why relevant:</em> {x['why_relevant']}<br>"
                     f"<em>How to emphasize:</em> {x['how_to_emphasize']}</li>"
        ),
        "General Suggestions": (
            analysis.get('general_suggestions', []),
            lambda x: f"<li>{x}</li>"
        )
    }
    
    formatted_sections = [
        format_section(title, items, formatter)
        for title, (items, formatter) in sections.items()
    ]
    
    return f"""
    <div class="optimization-results">
        {''.join(formatted_sections)}
    </div>
    """ 