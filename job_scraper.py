import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import json

class ScrapingError(Exception):
    """Custom exception for scraping errors"""
    pass

def extract_job_description(url: str) -> str:
    """Extract job description from various job posting sites"""
    try:
        print(f"\n[DEBUG] Starting extraction for URL: {url}")
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ScrapingError("Invalid URL format")

        print("[DEBUG] Making request with headers...")
        # Custom headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        print(f"[DEBUG] Response status code: {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')
        print("[DEBUG] Successfully parsed HTML")
        
        # Save the HTML content for debugging
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("[DEBUG] Saved HTML content to debug_page.html")
        
        # Identify the job site and use appropriate scraping strategy
        domain = parsed_url.netloc.lower()
        print(f"[DEBUG] Detected domain: {domain}")
        
        description = ""
        if 'github.careers' in domain or 'github.com' in domain:
            description = _scrape_github(soup, url)
        elif 'linkedin.com' in domain:
            description = _scrape_linkedin(soup)
        elif 'indeed.com' in domain:
            description = _scrape_indeed(soup)
        elif 'glassdoor.com' in domain:
            description = _scrape_glassdoor(soup)
        else:
            description = _scrape_generic(soup)

        print(f"\n[DEBUG] Extracted description length: {len(description)} characters")
        print("\n[DEBUG] First 500 characters of description:")
        print(description[:500] + "...")
        return description

    except requests.Timeout:
        print("[ERROR] Request timed out")
        raise ScrapingError("Request timed out. Please check your internet connection.")
    except requests.RequestException as e:
        print(f"[ERROR] Request exception: {str(e)}")
        if hasattr(e, 'response'):
            if e.response.status_code == 403:
                raise ScrapingError("Access denied. This job posting might require authentication.")
            elif e.response.status_code == 404:
                raise ScrapingError("Job posting not found. The link might be expired or invalid.")
        raise ScrapingError(f"Failed to fetch job posting: {str(e)}")
    except Exception as e:
        print(f"[ERROR] General exception: {str(e)}")
        raise ScrapingError(f"Failed to extract job description: {str(e)}")

def _scrape_github(soup: BeautifulSoup, url: str) -> str:
    """Extract job description from GitHub careers page"""
    try:
        print("[DEBUG] Starting GitHub scraping strategy")
        description = ""
        
        # Try different possible selectors for GitHub careers
        job_content_selectors = [
            'div[data-testid="jobDetails"]',
            'div.job-details',
            'div.job-description',
            'div[class*="description"]',
            'section[class*="description"]'
        ]
        
        print("[DEBUG] Trying to find content using selectors...")
        for selector in job_content_selectors:
            print(f"[DEBUG] Trying selector: {selector}")
            content = soup.select_one(selector)
            if content:
                print(f"[DEBUG] Found content with selector: {selector}")
                description = content.get_text(separator='\n', strip=True)
                break
        
        # If we can't find the content directly, try to extract the job ID
        if not description:
            print("[DEBUG] No content found with selectors, trying API approach...")
            job_id = re.search(r'/jobs/(\d+)', url)
            if job_id:
                print(f"[DEBUG] Found job ID: {job_id.group(1)}")
                # Try to fetch the job details from GitHub's API
                api_url = f"https://api.github.careers/api/jobs/{job_id.group(1)}"
                print(f"[DEBUG] Attempting API request to: {api_url}")
                headers = {'Accept': 'application/json'}
                try:
                    response = requests.get(api_url, headers=headers, timeout=10)
                    if response.ok:
                        job_data = response.json()
                        if 'description' in job_data:
                            description = job_data['description']
                            print("[DEBUG] Successfully retrieved description from API")
                except Exception as e:
                    print(f"[DEBUG] API request failed: {str(e)}")

        # If still no description, try parsing the HTML
        if not description:
            print("[DEBUG] Trying fallback HTML parsing...")
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|job', re.I))
            if main_content:
                print("[DEBUG] Found main content section")
                paragraphs = main_content.find_all(['p', 'li', 'div'], recursive=True)
                description = '\n'.join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50)

        if not description:
            print("[DEBUG] No description found using any method")
            raise ScrapingError("Could not find job description on GitHub careers page")

        # Clean up the description
        description = re.sub(r'\s+', ' ', description)
        description = re.sub(r'\n\s*\n', '\n\n', description)
        return description.strip()

    except Exception as e:
        print(f"[ERROR] GitHub scraping error: {str(e)}")
        raise ScrapingError(f"Error parsing GitHub careers page: {str(e)}")

def _scrape_linkedin(soup: BeautifulSoup) -> str:
    """Extract job description from LinkedIn"""
    description = soup.find('div', {'class': ['description__text', 'show-more-less-html']})
    if description:
        return description.get_text(strip=True)
    raise ScrapingError("Could not find job description on LinkedIn page")

def _scrape_indeed(soup: BeautifulSoup) -> str:
    """Extract job description from Indeed"""
    description = soup.find('div', {'id': 'jobDescriptionText'})
    if description:
        return description.get_text(strip=True)
    raise ScrapingError("Could not find job description on Indeed page")

def _scrape_glassdoor(soup: BeautifulSoup) -> str:
    """Extract job description from Glassdoor"""
    description = soup.find('div', {'class': 'jobDescriptionContent'})
    if description:
        return description.get_text(strip=True)
    raise ScrapingError("Could not find job description on Glassdoor page")

def _scrape_generic(soup: BeautifulSoup) -> str:
    """Generic scraping strategy for unknown job sites"""
    # Try common patterns for job descriptions
    possible_elements = [
        soup.find('div', {'class': re.compile(r'job.*description', re.I)}),
        soup.find('div', {'class': re.compile(r'description', re.I)}),
        soup.find('section', {'class': re.compile(r'description', re.I)}),
        soup.find(['div', 'section'], {'id': re.compile(r'job.*description', re.I)})
    ]
    
    for element in possible_elements:
        if element:
            text = element.get_text(strip=True)
            if len(text) > 100:  # Assume it's a valid description if it's long enough
                return text
    
    raise ScrapingError("Could not find job description on this page") 