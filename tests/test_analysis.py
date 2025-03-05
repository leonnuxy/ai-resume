import unittest
from flask import Flask, session, jsonify
from app.routes.analysis import analysis_bp
from app.routes.main import main_bp
from app.tasks import analyze_resume_task, celery  # Import celery
from unittest.mock import patch, MagicMock
import os
import json
from app import create_app
from datetime import datetime
from config.testing import TestConfig
from celery.exceptions import TimeoutError

class AnalysisTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test logging"""
        cls.log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_results')
        if not os.path.exists(cls.log_dir):
            os.makedirs(cls.log_dir)
        
        # Create a log file with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        cls.log_file = os.path.join(cls.log_dir, f'flask_analysis_test_{timestamp}.log')

    def setUp(self):
        """Set up test case with Flask test client"""
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

        # Sample test data
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

    def tearDown(self):
        self.ctx.pop()

    def log_result(self, test_name: str, result: dict, additional_info: str = None):
        """Log test results to file"""
        with open(self.log_file, 'a') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"Test: {test_name}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*50}\n\n")
            
            if additional_info:
                f.write(f"Additional Info:\n{additional_info}\n\n")
            
            f.write("Response:\n")
            f.write(json.dumps(result, indent=2))
            f.write("\n\n")

    @patch('app.routes.analysis.analyze_resume_task.delay')
    def test_optimize_resume_valid_input(self, mock_analyze_resume_task):
        """Test optimize_resume with valid input."""
        mock_analyze_resume_task.return_value.id = 'test_task_id'

        with self.client.session_transaction() as sess:
            sess['modified_text'] = 'Sample resume text'

        response = self.client.post('/analysis/optimize', 
            data={'job_description': 'Looking for Senior Developer with AWS skills'},
            headers={'Accept': 'application/json'},
            follow_redirects=False)

        self.assertEqual(response.status_code, 202)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['task_id'], 'test_task_id')

    @patch('app.routes.analysis.analyze_resume_task.delay')
    def test_optimize_resume_missing_input(self, mock_analyze_resume_task):
        """Test optimize_resume with missing input."""
        with self.client.session_transaction() as sess:
            sess['modified_text'] = ''

        response = self.client.post('/analysis/optimize', data={
            'job_description': ''
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please provide both resume text and job description', response.data)

    @patch('app.routes.analysis.celery.AsyncResult')
    def test_get_task_status_success(self, mock_async_result):
        """Test getting the status of a successful task."""
        mock_task = MagicMock()
        mock_task.state = 'SUCCESS'
        mock_task.info = None
        mock_task.result = {'result': {'key': 'value'}}
        mock_task.backend = None
        mock_async_result.return_value = mock_task

        response = self.client.get('/analysis/status/test_task_id')
        json_data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json_data['state'], 'SUCCESS')
        chunk_data = json.loads(json_data['chunk'])
        self.assertEqual(chunk_data['status'], 'completed')
        self.assertIn('key', chunk_data['result'])

    @patch('app.routes.analysis.analyze_resume_task.AsyncResult')
    def test_get_task_status_pending(self, mock_async_result):
        """Test getting the status of a pending task."""
        mock_task = MagicMock()
        mock_task.state = 'PENDING'
        mock_task.info = {'status': 'Task is pending...'}
        mock_async_result.return_value = mock_task

        response = self.client.get('/analysis/status/test_task_id')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['state'], 'PENDING')
        self.assertEqual(response.get_json()['status'], 'Task is pending...')

    @patch('app.routes.analysis.celery.AsyncResult')
    def test_get_task_status_failure(self, mock_async_result):
        """Test getting the status of a failed task."""
        error_message = 'Task failed'
        mock_task = MagicMock()
        mock_task.state = 'FAILURE'
        mock_task.info = error_message
        mock_task.backend = None
        mock_async_result.return_value = mock_task

        response = self.client.get('/analysis/status/test_task_id')
        json_data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json_data['state'], 'FAILURE')
        self.assertEqual(json_data['status'], error_message)

    def test_fetch_job_description_valid(self):
        """Test fetch_job_description with valid URL."""
        with patch('app.routes.analysis.extract_job_description') as mock_extract:
            mock_extract.return_value = 'Sample job description'
            response = self.client.post('/analysis/fetch_job_description', json={'url': 'http://example.com'}, headers={'Accept': 'application/json'})

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()['description'], 'Sample job description')

    def test_fetch_job_description_invalid_url(self):
        """Test fetch_job_description with invalid URL."""
        with patch('app.routes.analysis.extract_job_description') as mock_extract:
            mock_extract.side_effect = Exception('Failed to fetch')
            response = self.client.post('/analysis/fetch_job_description', json={'url': 'invalid_url'}, headers={'Accept': 'application/json'})

            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.get_json()['error'], 'Failed to fetch job description')

    def test_fetch_job_description_no_url(self):
        """Test fetch_job_description with no URL provided."""
        response = self.client.post('/analysis/fetch_job_description', json={}, headers={'Accept': 'application/json'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()['error'], 'No URL provided')

    def test_ollama_connection_endpoint(self):
        """Test the Ollama connection endpoint"""
        with patch('app.routes.analysis.test_ollama_connection', return_value=True):
            response = self.client.get('/analysis/test_ollama')
            data = json.loads(response.data)
            
            self.assertEqual(response.status_code, 200)
            self.assertTrue(data['connected'])
            
            self.log_result(
                'test_ollama_connection_endpoint',
                data,
                'Testing the /analysis/test_ollama endpoint'
            )

    def test_optimize_resume_endpoint(self):
        """Test the resume optimization endpoint"""
        with self.client.session_transaction() as session:
            session['modified_text'] = self.sample_resume

        with patch('app.routes.analysis.analyze_resume_task.delay') as mock_task:
            mock_task.return_value.id = 'test_task_id'
            
            # Test JSON response
            response = self.client.post(
                '/analysis/optimize',
                data={'job_description': self.sample_job},
                headers={'Accept': 'application/json'}
            )
            
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 202)
            self.assertIn('task_id', data)
            
            self.log_result(
                'test_optimize_resume_endpoint',
                data,
                'Testing the /analysis/optimize endpoint with JSON response'
            )

            # Test HTML response
            response = self.client.post(
                '/analysis/optimize',
                data={'job_description': self.sample_job}
            )
            
            self.assertEqual(response.status_code, 200)
            # Check for content that exists in the rendered processing.html template
            self.assertIn(b'Processing your resume...', response.data)
            self.assertIn(b'Live Analysis Progress', response.data)
            
            self.log_result(
                'test_optimize_resume_endpoint_html',
                {'status_code': response.status_code},
                'Testing the /analysis/optimize endpoint with HTML response'
            )

    def test_fetch_job_description_endpoint(self):
        """Test the job description fetching endpoint"""
        test_url = "https://example.com/job"
        test_description = "Test job description"
        
        with patch('app.routes.analysis.extract_job_description', return_value=test_description):
            response = self.client.post(
                '/analysis/fetch_job_description',
                json={'url': test_url}
            )
            
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['description'], test_description)
            
            self.log_result(
                'test_fetch_job_description_endpoint',
                data,
                f'Testing job description fetch from URL: {test_url}'
            )

    def test_task_status_endpoint(self):
        """Test the task status checking endpoint"""
        test_task_id = 'test_task_id'
        test_result = {
            'result': {
                'missing_skills': ['AWS'],
                'improvement_suggestions': ['Add cloud experience'],
                'emphasis_suggestions': ['Highlight Python skills'],
                'general_suggestions': ['Update summary']
            }
        }
        
        with patch('app.routes.analysis.celery.AsyncResult') as mock_result:
            # Test pending state
            mock_result.return_value.state = 'PENDING'
            response = self.client.get(f'/analysis/status/{test_task_id}')
            data = json.loads(response.data)
            self.assertEqual(data['state'], 'PENDING')
            
            # Test success state
            mock_result.return_value.state = 'SUCCESS'
            mock_result.return_value.result = test_result
            response = self.client.get(f'/analysis/status/{test_task_id}')
            data = json.loads(response.data)
            self.assertEqual(data['state'], 'SUCCESS')
            
            self.log_result(
                'test_task_status_endpoint',
                data,
                f'Testing task status endpoint for task ID: {test_task_id}'
            )

    def test_invalid_inputs(self):
        """Test handling of invalid inputs"""
        # Test empty job description
        with self.client.session_transaction() as session:
            session['modified_text'] = self.sample_resume

        response = self.client.post(
            '/analysis/optimize',
            data={'job_description': ''},
            headers={'Accept': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 400)
        
        # Test missing URL in job description fetch
        response = self.client.post(
            '/analysis/fetch_job_description',
            json={}
        )
        
        self.assertEqual(response.status_code, 400)
        
        self.log_result(
            'test_invalid_inputs',
            {
                'empty_job_description_status': response.status_code,
                'missing_url_status': response.status_code
            },
            'Testing handling of invalid inputs'
        )

    def test_task_timeout(self):
        """Test handling of task timeout"""
        test_task_id = 'timeout_task_id'
        
        with patch('app.routes.analysis.celery.AsyncResult') as mock_result:
            # Simulate a timeout
            mock_result.return_value.get.side_effect = TimeoutError()
            mock_result.return_value.state = 'PENDING'
            
            response = self.client.get(f'/analysis/status/{test_task_id}')
            data = json.loads(response.data)
            
            self.assertEqual(response.status_code, 408)  # Timeout status
            self.assertIn('error', data)
            
            self.log_result(
                'test_task_timeout',
                data,
                'Testing timeout handling in task processing'
            )

    def test_task_progress_reporting(self):
        """Test task progress updates"""
        test_task_id = 'progress_task_id'
        
        with patch('app.routes.analysis.celery.AsyncResult') as mock_result:
            # Simulate task in progress
            mock_result.return_value.state = 'PROGRESS'
            mock_result.return_value.info = {
                'current': 50,
                'total': 100,
                'status': 'Analyzing resume...'
            }
            
            response = self.client.get(f'/analysis/status/{test_task_id}')
            data = json.loads(response.data)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['state'], 'PROGRESS')
            self.assertIn('current', json.loads(data['chunk']))
            
            self.log_result(
                'test_task_progress_reporting',
                data,
                'Testing progress reporting in task processing'
            )

    def test_celery_worker_connection(self):
        """Test Celery worker connectivity"""
        with patch('app.routes.analysis.celery.control.inspect') as mock_inspect:
            # Simulate active workers
            mock_inspect.return_value.active.return_value = {'worker1@localhost': []}
            
            # Test worker connectivity through the application
            with patch('app.routes.analysis.analyze_resume_task.delay') as mock_task:
                mock_task.return_value.id = 'test_task_id'
                
                response = self.client.post(
                    '/analysis/optimize',
                    data={'job_description': self.sample_job},
                    headers={'Accept': 'application/json'}
                )
                
                self.assertEqual(response.status_code, 202)
                self.assertTrue(mock_task.called)

    def test_task_cancellation(self):
        """Test task cancellation handling"""
        test_task_id = 'cancel_task_id'
        
        with patch('app.routes.analysis.celery.AsyncResult') as mock_result:
            # Simulate task revocation
            mock_result.return_value.state = 'REVOKED'
            
            response = self.client.get(f'/analysis/status/{test_task_id}')
            data = json.loads(response.data)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['state'], 'REVOKED')
            
            self.log_result(
                'test_task_cancellation',
                data,
                'Testing task cancellation handling'
            )

    def test_long_running_task_monitoring(self):
        """Test monitoring of long-running tasks"""
        test_task_id = 'long_running_task_id'
        
        with patch('app.routes.analysis.celery.AsyncResult') as mock_result:
            # Simulate a long-running task
            mock_result.return_value.state = 'PROGRESS'
            mock_result.return_value.info = {
                'current': 75,
                'total': 100,
                'status': 'Processing large resume...',
                'execution_time': 3600  # 1 hour
            }
            
            response = self.client.get(f'/analysis/status/{test_task_id}')
            data = json.loads(response.data)
            
            self.assertEqual(response.status_code, 200)
            chunk_data = json.loads(data['chunk'])
            self.assertIn('execution_time', chunk_data)
            
            self.log_result(
                'test_long_running_task_monitoring',
                data,
                'Testing long-running task monitoring'
            )

if __name__ == '__main__':
    unittest.main()