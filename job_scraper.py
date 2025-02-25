import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re

class ScrapingError(Exception):
    """Custom exception for scraping errors."""
    pass

# Candidate phrases for important sections
IMPORTANT_SECTIONS = {
    "role": [
        "job description",
        "role and responsibilities",
        "role",
        "what you will do",
        "job duties",
        "key responsibilities",
        "position overview",
        "your role",
        "duties and responsibilities"
    ],
    "qualifications": [
        "qualifications",
        "required qualifications",
        "preferred qualifications",
        "job requirements",
        "requirements",
        "skills and experience",
        "required skills",
        "essential skills",
        "experience",
        "key requirements"
    ],
    "additional": [
        "about the role",
        "overview",
        "summary",
        "essential functions",
        "who we are",
        "about us"
    ]
}

def _clean_description(text: str) -> str:
    """
    Cleans the extracted text by removing extraneous navigation,
    header, footer, and known noise patterns.
    """
    ignore_patterns = [
        r'Toggle navigation.*?(?=ProductActions)',  # Example: navigation block
        r'Join Our Talent Community.*',
        r'Subscribe to our.*?inbox\.',
        r'©\s*\d{4}.*'
    ]
    for pattern in ignore_patterns:
        text = re.sub(pattern, '', text, flags=re.DOTALL)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def _scrape_by_candidate_sections(soup: BeautifulSoup) -> str:
    """
    Dynamically extracts content based on candidate section headings.
    Scans all heading tags (h1-h6) for keywords that denote important job posting sections.
    """
    extracted_sections = []
    for heading in soup.find_all(re.compile('^h[1-6]$')):
        heading_text = heading.get_text(separator=' ', strip=True).lower()
        for category, keywords in IMPORTANT_SECTIONS.items():
            for keyword in keywords:
                if keyword in heading_text:
                    # If heading matches a candidate phrase, collect its text and subsequent siblings.
                    section_text = heading.get_text(separator=' ', strip=True)
                    sibling = heading.find_next_sibling()
                    while sibling and sibling.name not in ['h1','h2','h3','h4','h5','h6']:
                        section_text += " " + sibling.get_text(separator=' ', strip=True)
                        sibling = sibling.find_next_sibling()
                    if len(section_text) > 50:
                        extracted_sections.append(section_text)
                    break  # Keyword match found; no need to check other keywords in this heading.
    if extracted_sections:
        return _clean_description(" ".join(extracted_sections))
    return ""

def extract_job_description(url: str) -> str:
    """
    Extracts the job description text from a job posting URL.
    Uses specialized strategies for known domains and falls back to candidate-based extraction.
    """
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        raise ScrapingError("Invalid URL format")
    
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/91.0.4472.124 Safari/537.36'
        ),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.Timeout:
        raise ScrapingError("Request timed out. Please check your internet connection.")
    except requests.RequestException as e:
        if hasattr(e, 'response'):
            if e.response.status_code == 403:
                raise ScrapingError("Access denied. This job posting might require authentication.")
            elif e.response.status_code == 404:
                raise ScrapingError("Job posting not found. The link might be expired or invalid.")
        raise ScrapingError(f"Failed to fetch job posting: {str(e)}")

    soup = BeautifulSoup(response.text, 'html.parser')
    domain = parsed_url.netloc.lower()

    # Use specialized strategies for known domains
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

    # If extraction is still insufficient, fall back to candidate section extraction.
    if not description or len(description) < 100:
        candidate_text = _scrape_by_candidate_sections(soup)
        if candidate_text and len(candidate_text) > 100:
            description = candidate_text

    if not description or len(description) < 100:
        raise ScrapingError("Failed to extract a sufficient job description from the page."+description)
    return description

def _scrape_github(soup: BeautifulSoup) -> str:
    """
    Extract job description from GitHub-related pages.
    Tries a set of selectors and a fallback article with id 'description-body'.
    """
    selectors = [
        'div[data-testid="jobDetails"]',
        'div.job-details',
        'div.job-description',
        'div[class*="description"]',
        'section[class*="description"]'
    ]
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(separator='\n', strip=True)
            if len(text) > 100:
                return _clean_description(text)
    main_article = soup.find('article', id="description-body")
    if main_article:
        text = main_article.get_text(separator='\n', strip=True)
        if len(text) > 100:
            return _clean_description(text)
    return ""

def _scrape_linkedin(soup: BeautifulSoup) -> str:
    """Extract job description from LinkedIn pages."""
    selectors = [
        'div.description__text',
        'div.show-more-less-html'
    ]
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(separator='\n', strip=True)
            if len(text) > 100:
                return _clean_description(text)
    return ""

def _scrape_indeed(soup: BeautifulSoup) -> str:
    """Extract job description from Indeed pages."""
    element = soup.find('div', {'id': 'jobDescriptionText'})
    if element:
        text = element.get_text(separator='\n', strip=True)
        if len(text) > 100:
            return _clean_description(text)
    return ""

def _scrape_glassdoor(soup: BeautifulSoup) -> str:
    """Extract job description from Glassdoor pages."""
    element = soup.find('div', {'class': 'jobDescriptionContent'})
    if element:
        text = element.get_text(separator='\n', strip=True)
        if len(text) > 100:
            return _clean_description(text)
    return ""

def _scrape_generic(soup: BeautifulSoup) -> str:
    """
    Generic scraping strategy for unknown job sites.
    First tries common selectors, then falls back to candidate section extraction.
    """
    possible_selectors = [
        'div[class*="job"][class*="description"]',
        'div[class*="description"]',
        'main',
        'article'
    ]
    for selector in possible_selectors:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(separator='\n', strip=True)
            if len(text) > 100:
                return _clean_description(text)
    return ""

# Example usage:
# try:
#     job_text = extract_job_description("https://www.example.com/job-posting")
#     print(job_text)
# except ScrapingError as e:
#     print("Error:", e)
