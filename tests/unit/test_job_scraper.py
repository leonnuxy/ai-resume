import sys
import os
import time
from datetime import datetime
from typing import List, Dict

# Add parent directory to path to import job_scraper
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.job_scraper import extract_job_description, ScrapingError

class JobScraperTester:
    def __init__(self):
        self.test_urls = [
            {
                "url": "https://www.github.careers/careers-home/jobs/3345?lang=en-us",
                "name": "GitHub Careers Job",
                "expected_content_markers": ["responsibilities"]
            },
            # Add more test URLs here
        ]
        self.results_dir = "test_results"
        os.makedirs(self.results_dir, exist_ok=True)

    def run_tests(self):
        """Run tests for all URLs in the test set"""
        print("\n=== Starting Job Scraper Tests ===")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        results = []
        for test_case in self.test_urls:
            result = self._test_single_url(test_case)
            results.append(result)
            print("\n" + "="*50 + "\n")

        self._save_results(results)
        self._print_summary(results)

    def _test_single_url(self, test_case: Dict) -> Dict:
        """Test a single URL and return the results"""
        url = test_case["url"]
        name = test_case["name"]
        expected_markers = test_case.get("expected_content_markers", [])

        print(f"Testing: {name}")
        print(f"URL: {url}")
        
        result = {
            "name": name,
            "url": url,
            "success": False,
            "error": None,
            "description_length": 0,
            "markers_found": [],
            "execution_time": 0
        }

        try:
            start_time = time.time()
            description = extract_job_description(url)
            result["execution_time"] = time.time() - start_time

            # Basic validation
            if description:
                result["success"] = True
                result["description_length"] = len(description)
                
                # Check for expected content markers
                for marker in expected_markers:
                    if marker.lower() in description.lower():
                        result["markers_found"].append(marker)

                # Save the description to a file
                filename = f"{self.results_dir}/{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"URL: {url}\n")
                    f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*50 + "\n\n")
                    f.write(description)

                print(f"\nSuccess! Description length: {len(description)} characters")
                print(f"Expected markers found: {len(result['markers_found'])}/{len(expected_markers)}")
                print(f"Description saved to: {filename}")
            else:
                result["error"] = "Empty description returned"
                print("\nError: Empty description returned")

        except ScrapingError as e:
            result["error"] = str(e)
            print(f"\nScraping Error: {e}")
        except Exception as e:
            result["error"] = str(e)
            print(f"\nUnexpected Error: {e}")

        print(f"\nExecution time: {result['execution_time']:.2f} seconds")
        return result

    def _save_results(self, results: List[Dict]):
        """Save test results to a summary file"""
        filename = f"{self.results_dir}/summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=== Job Scraper Test Results ===\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for result in results:
                f.write(f"Test: {result['name']}\n")
                f.write(f"URL: {result['url']}\n")
                f.write(f"Success: {result['success']}\n")
                f.write(f"Description Length: {result['description_length']}\n")
                f.write(f"Markers Found: {', '.join(result['markers_found'])}\n")
                f.write(f"Execution Time: {result['execution_time']:.2f} seconds\n")
                if result['error']:
                    f.write(f"Error: {result['error']}\n")
                f.write("\n" + "="*30 + "\n\n")

    def _print_summary(self, results: List[Dict]):
        """Print a summary of all test results"""
        print("\n=== Test Summary ===")
        successful_tests = sum(1 for r in results if r['success'])
        print(f"Total Tests: {len(results)}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {len(results) - successful_tests}")
        print("\nDetailed Results:")
        for result in results:
            status = "✓" if result['success'] else "✗"
            print(f"{status} {result['name']}: {'Success' if result['success'] else result['error']}")

def add_test_url(url: str, name: str, expected_markers: List[str] = None):
    """Add a new test URL to the test set"""
    tester = JobScraperTester()
    tester.test_urls.append({
        "url": url,
        "name": name,
        "expected_content_markers": expected_markers or []
    })
    return tester

if __name__ == "__main__":
    # Create and run the tester
    tester = JobScraperTester()
    
    # You can add more test URLs here
    tester.test_urls.extend([
        {
            "url": "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4160350287&origin=JYMBII_IN_APP_NOTIFICATION&originToLandingJobPostings=4158636844%2C4163610527",
            "name": "LinkedIn Job",
            "expected_content_markers": ["responsibilities", "requirements", "qualifications", "experience", "skills"]
        },
        {
            "url": "https://jobs.ledcor.com/jobs/15692451-system-solutions-developer",
            "name": "Ledcor Job",
            "expected_content_markers": ["qualifications", "experience", "skills", "responsibilities", "requirements"]
        },
        {
            "url": "https://www.github.careers/careers-home/jobs/3345?lang=en-us",
            "name": "GitHub Careers Job",
            "expected_content_markers": ["responsibilities", "qualifications", "requirements", "experience", "skills"]
        }
    ])
    
    # Run the tests
    tester.run_tests() 