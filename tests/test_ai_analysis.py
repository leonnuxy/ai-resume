import unittest
from app.services.ai_analysis import analyze_resume_for_job, test_ollama_connection
import json
import os
from datetime import datetime

class AIAnalysisTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test logging"""
        cls.log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_results')
        if not os.path.exists(cls.log_dir):
            os.makedirs(cls.log_dir)
        
        # Create a log file with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        cls.log_file = os.path.join(cls.log_dir, f'ai_analysis_test_{timestamp}.log')
        
    def log_result(self, test_name: str, result: dict, additional_info: str = None):
        """Log test results to file"""
        with open(self.log_file, 'a') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"Test: {test_name}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*50}\n\n")
            
            if additional_info:
                f.write(f"Additional Info:\n{additional_info}\n\n")
            
            f.write("Analysis Result:\n")
            f.write(json.dumps(result, indent=2))
            f.write("\n\n")

    def setUp(self):
        """Set up test case with sample resume and job description"""
        self.sample_resume = """
        John Doe
        Software Engineer
        
        Experience:
        - Senior Developer at Tech Corp (2018-Present)
          * Led team of 5 developers
          * Implemented cloud solutions
        
        Skills:
        - Python, JavaScript, Docker
        - Agile methodologies
        """
        
        self.sample_job = """
        Senior Software Engineer
        
        Requirements:
        - 5+ years of experience in Python
        - Experience with AWS and cloud technologies
        - Strong leadership skills
        - Knowledge of React and modern JavaScript
        """

    def test_ollama_connection(self):
        """Test that we can connect to Ollama service"""
        result = test_ollama_connection()
        self.assertTrue(result, "Should be able to connect to Ollama service")
        self.log_result("test_ollama_connection", 
                       {"connection_successful": result},
                       "Testing connection to Ollama service")

    def test_resume_analysis(self):
        """Test that resume analysis returns properly structured data"""
        result = analyze_resume_for_job(self.sample_resume, self.sample_job)
        
        # Verify the response structure
        self.assertIsInstance(result, dict)
        self.assertIn('missing_skills', result)
        self.assertIn('improvement_suggestions', result)
        self.assertIn('emphasis_suggestions', result)
        self.assertIn('general_suggestions', result)
        
        # Verify that all required fields are lists
        self.assertIsInstance(result['missing_skills'], list)
        self.assertIsInstance(result['improvement_suggestions'], list)
        self.assertIsInstance(result['emphasis_suggestions'], list)
        self.assertIsInstance(result['general_suggestions'], list)
        
        # Log the results
        summary = (
            f"Missing Skills: {len(result['missing_skills'])}\n"
            f"Improvements: {len(result['improvement_suggestions'])}\n"
            f"Emphasis Points: {len(result['emphasis_suggestions'])}\n"
            f"General Suggestions: {len(result['general_suggestions'])}"
        )
        self.log_result("test_resume_analysis", result, summary)

    def test_response_relevance(self):
        """Test that the AI provides relevant analysis"""
        result = analyze_resume_for_job(self.sample_resume, self.sample_job)
        
        # Combined test for skill analysis (either missing or emphasized)
        aws_analyzed = any('aws' in skill['skill'].lower() for skill in result['missing_skills']) or \
                      any('aws' in sugg['experience'].lower() for sugg in result['emphasis_suggestions'])
        
        python_analyzed = any('python' in skill['skill'].lower() for skill in result['missing_skills']) or \
                         any('python' in sugg['experience'].lower() for sugg in result['emphasis_suggestions'])
        
        # At least one of the key skills should be analyzed
        self.assertTrue(
            aws_analyzed or python_analyzed,
            "Analysis should mention either AWS or Python skills"
        )
        
        # Prepare summary for logging
        skill_summary = []
        if len(result['missing_skills']) > 0:
            skill_summary.append("Missing Skills:")
            for skill in result['missing_skills']:
                skill_summary.append(f"- {skill['skill']}: {skill['suggestion']}")
        
        if len(result['emphasis_suggestions']) > 0:
            skill_summary.append("\nEmphasis Suggestions:")
            for sugg in result['emphasis_suggestions']:
                skill_summary.append(f"- {sugg['experience']}: {sugg['how_to_emphasize']}")
        
        self.log_result("test_response_relevance", 
                       result,
                       "\n".join(skill_summary))

if __name__ == '__main__':
    unittest.main()