import requests
from bs4 import BeautifulSoup
import re
import logging

logger = logging.getLogger(__name__)

def clean_article_text(url, max_retries=3):
    """Extract and clean article content from URL with multiple strategies"""
    
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; VC-Thesis-Bot/1.0)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(url, timeout=15, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 
                               'aside', 'advertisement', '.ad', '.ads']):
                element.decompose()
            
            # Try multiple content extraction strategies
            content = extract_main_content(soup)
            
            if not content or len(content.strip()) < 50:
                logger.warning(f"Insufficient content extracted from {url}")
                return ""
            
            return clean_text(content)
            
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
            if attempt == max_retries - 1:
                return ""
        except Exception as e:
            logger.error(f"Unexpected error extracting content from {url}: {e}")
            return ""

def extract_main_content(soup):
    """Extract main content using multiple strategies"""
    
    # Strategy 1: Look for common article containers
    article_selectors = [
        'article',
        '.post-content',
        '.entry-content', 
        '.content',
        '.post-body',
        '.article-content',
        'main',
        '.main-content',
        '[role="main"]'
    ]
    
    for selector in article_selectors:
        content_div = soup.select_one(selector)
        if content_div:
            paragraphs = content_div.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if paragraphs:
                text = '\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                if len(text) > 100:  # If we got substantial content
                    return text
    
    # Strategy 2: Look for the largest text container
    all_divs = soup.find_all('div')
    best_div = None
    max_text_length = 0
    
    for div in all_divs:
        paragraphs = div.find_all('p')
        if len(paragraphs) >= 3:  # At least 3 paragraphs
            text_length = len(' '.join(p.get_text() for p in paragraphs))
            if text_length > max_text_length:
                max_text_length = text_length
                best_div = div
    
    if best_div:
        paragraphs = best_div.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        text = '\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        if len(text) > 100:
            return text
    
    # Strategy 3: Fallback to all paragraphs
    paragraphs = soup.find_all('p')
    return '\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

def clean_text(text):
    """Clean extracted text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common navigation/footer text
    unwanted_patterns = [
        r'Get in Touch.*',
        r'Dark Mode.*',
        r'Made with.*',
        r'Copyright.*',
        r'All rights reserved.*',
        r'Follow us.*',
        r'Subscribe.*',
        r'Share this.*',
        r'Contact us.*'
    ]
    
    for pattern in unwanted_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Clean up extra spaces again
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
