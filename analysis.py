import json
import ollama
from typing import Dict, List, Tuple

def analyze_document_structure(text: str) -> dict:
    """Use Ollama to analyze document structure and formatting"""
    try:
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
        
        response = ollama.chat(model='mistral', messages=[{
            'role': 'user',
            'content': prompt
        }])
        
        # Extract JSON from response
        analysis = json.loads(response['message']['content'])
        return analysis
    except Exception as e:
        print(f"AI analysis error: {str(e)}")
        return {}

def analyze_resume_sections(text: str) -> dict:
    """Use Ollama to analyze and identify resume sections"""
    try:
        # Define the standard sections and their subsections
        standard_sections = {
            'Skills': [
                '• Languages: Python, Java, C#, Go, Scala, C++, SQL, JavaScript(React) and HTML/CSS',
                '• Cloud & DevOps: Kubernetes, Google Cloud, Azure Kubernetes Services, AWS, Jenkins, Docker, and Kafka',
                '• Methodologies: Agile (Scrum), Continuous Integration/Continuous Deployment (CI/CD), Jira, Confluence, SDLC',
                '• Web Development: React, Selenium, REST APIs, Spring Boot, .NET, Node.js, PostgreSQL, MongoDB, MySQL',
                '• Data Analysis: Power BI, Tableau, Power Query, and advanced Microsoft Excel',
                '• Data Infrastructure: ETM deliverables, Snowflake, Azure Data Services, and Operational Data Store (ODS)'
            ],
            'Experience': [],  # Will be populated by AI analysis
            'Achievements': [],
            'Education': [],
            'Certifications': []
        }

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

        response = ollama.chat(model='mistral', messages=[{
            'role': 'user',
            'content': prompt
        }])
        
        analysis = json.loads(response['message']['content'])
        
        # Ensure all required sections exist with proper subsections
        sections = []
        for section_name, default_subsections in standard_sections.items():
            # Find existing section if it exists
            existing_section = next(
                (s for s in analysis.get('sections', []) if s['name'] == section_name),
                None
            )
            
            content = []
            if section_name == 'Skills':
                # Use predefined skill subsections
                content = default_subsections
            elif existing_section:
                # Use AI-analyzed content for other sections
                content = existing_section.get('content', [])
            
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
        
        return {
            'sections': sections,
            'structure_analysis': {
                'section_order': list(standard_sections.keys()),
                'hierarchy': {
                    'main_sections': list(standard_sections.keys()),
                    'subsections': {}
                }
            }
        }
    except Exception as e:
        print(f"Error in resume section analysis: {str(e)}")
        return {
            'sections': [
                {
                    'name': section_name,
                    'type': 'main_section',
                    'content': subsections if section_name == 'Skills' else [],
                    'formatting': {
                        'is_header': True,
                        'suggested_font_size': 12,
                        'suggested_spacing': 1.5
                    }
                } for section_name, subsections in standard_sections.items()
            ],
            'structure_analysis': {
                'section_order': list(standard_sections.keys()),
                'hierarchy': {
                    'main_sections': list(standard_sections.keys()),
                    'subsections': {}
                }
            }
        }

def analyze_resume_for_job(resume_text: str, job_description: str) -> dict:
    """Use Ollama to analyze and optimize resume for a specific job"""
    try:
        # First, ensure we have valid input
        if not resume_text or not job_description:
            print("Missing required input for analysis")
            return {}

        # Structure the prompt more clearly
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

        # Make the API call with error handling
        try:
            response = ollama.chat(model='mistral', messages=[{
                'role': 'user',
                'content': prompt
            }])
            
            # Validate and parse the response
            if not response or not response.get('message') or not response['message'].get('content'):
                print("Invalid response from AI model")
                return {}
            
            analysis = json.loads(response['message']['content'])
            
            # Validate the analysis structure
            required_keys = ['missing_skills', 'improvement_suggestions', 
                           'emphasis_suggestions', 'general_suggestions']
            
            if not all(key in analysis for key in required_keys):
                print("Incomplete analysis structure")
                return {key: [] for key in required_keys}
            
            return analysis
            
        except json.JSONDecodeError as e:
            print(f"Error parsing AI response: {str(e)}")
            return {}
        except Exception as e:
            print(f"Error in AI analysis: {str(e)}")
            return {}
            
    except Exception as e:
        print(f"Error in resume analysis: {str(e)}")
        return {
            "missing_skills": [],
            "improvement_suggestions": [],
            "emphasis_suggestions": [],
            "general_suggestions": [
                "Unable to complete analysis. Please try again."
            ]
        }

def format_optimization_suggestions(analysis: dict) -> str:
    """Format the AI analysis into HTML"""
    if not analysis:
        return "<p>Unable to generate optimization suggestions. Please try again.</p>"
    
    html = []
    
    # Helper function to format a section
    def format_section(title: str, items: list, formatter) -> None:
        if items:
            html.append(f"<h4>{title}</h4><ul>")
            for item in items:
                html.append(formatter(item))
            html.append("</ul>")
    
    # Missing Skills
    format_section(
        "Missing Key Skills",
        analysis.get('missing_skills', []),
        lambda x: f"<li><strong>{x['skill']}</strong>: {x['suggestion']}</li>"
    )
    
    # Improvement Suggestions
    format_section(
        "Suggested Improvements",
        analysis.get('improvement_suggestions', []),
        lambda x: f"<li><div class='highlight'>{x['current']}</div> could be improved to: "
                 f"<div class='highlight'>{x['suggested']}</div>"
                 f"<em>Why: {x['reason']}</em></li>"
    )
    
    # Emphasis Suggestions
    format_section(
        "Experiences to Emphasize",
        analysis.get('emphasis_suggestions', []),
        lambda x: f"<li><strong>{x['experience']}</strong>"
                 f"<br>Relevance: {x['why_relevant']}"
                 f"<br>Suggestion: {x['how_to_emphasize']}</li>"
    )
    
    # General Suggestions
    format_section(
        "General Suggestions",
        analysis.get('general_suggestions', []),
        lambda x: f"<li>{x}</li>"
    )
    
    if not html:
        return "<p>No specific suggestions found. Your resume might already be well-matched for this position.</p>"
    
    return "\n".join(html) 