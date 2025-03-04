import json
import ollama
import logging
from typing import Dict



# Configure logging
logging.config.fileConfig('logging_config.ini')
logger = logging.getLogger('analysis')

# Constants
LOG_SENDING_PROMPT = "Sending prompt to Ollama"

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
        # Construct the final result dictionary in the correct format.
        result = {
            'analysis': analysis,  # All the analysis data is under 'analysis'
            'suggestions': []     # Initialize 'suggestions' as an empty list

        }
         # Create suggestions list
        for item in analysis.get('missing_skills', []):
            result['suggestions'].append(f"Missing Skill: {item.get('skill', '')} - {item.get('suggestion', '')}")
        for item in analysis.get('improvement_suggestions', []):
            result['suggestions'].append(f"Improve: {item.get('current', '')} -> {item.get('suggested', '')} ({item.get('reason', '')})")
        for item in analysis.get('emphasis_suggestions', []):
            result['suggestions'].append(f"Emphasize: {item.get('experience', '')} ({item.get('why_relevant', '')} - {item.get('how_to_emphasize','')})")
        for item in analysis.get('general_suggestions', []):
            result['suggestions'].append(f"General: {item}")

        logger.info("Successfully completed resume optimization analysis")

        return result

    except Exception as e:
        logger.error(f"Error in resume optimization analysis: {str(e)}", exc_info=True)
        return {
            "analysis": {
                "missing_skills": [],
                "improvement_suggestions": [],
                "emphasis_suggestions": [],
                "general_suggestions": []
            },
            "suggestions": [  # Add the suggestions key here
                "Unable to complete analysis.  Please try again."
            ]
        }

# Ensure the function is exported
__all__ = ['analyze_resume_for_job']
